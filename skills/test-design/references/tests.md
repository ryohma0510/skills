# 良いテストと悪いテスト

## 良いテスト

**統合スタイル（integration-style）**: 内部をモックするのではなく、本物のインターフェースを通してテストする。

```typescript
// GOOD: Tests observable behavior
test("should confirm the order when the cart has items", async () => {
  // Given
  const cart = createCart();
  cart.add(product);

  // When
  const result = await checkout(cart, paymentMethod);

  // Then
  expect(result.status).toBe("confirmed");
});
```

特徴:

- 利用者/呼び出し側が気にする振る舞いをテストしている
- 公開 API だけを使っている
- 内部のリファクタを生き延びる
- HOW ではなく WHAT を記述している
- 1テストにつき論理的なアサーションは1つ

## 悪いテスト

**実装詳細のテスト**: 内部構造に結合している。

```typescript
// BAD: Tests implementation details
test("checkout calls paymentService.process", async () => {
  const mockPayment = jest.mock(paymentService);
  await checkout(cart, payment);
  expect(mockPayment.process).toHaveBeenCalledWith(cart.total);
});
```

危険信号:

- 内部の協力オブジェクトをモックしている
- プライベートメソッドをテストしている
- 呼び出し回数/順序をアサートしている
- 振る舞いを変えないリファクタでテストが壊れる
- テスト名が WHAT ではなく HOW を説明している
- インターフェースではなく外部の手段を通じて検証している

```typescript
// BAD: Bypasses interface to verify
test("createUser saves to database", async () => {
  await createUser({ name: "Alice" });
  const row = await db.query("SELECT * FROM users WHERE name = ?", ["Alice"]);
  expect(row).toBeDefined();
});

// GOOD: Verifies through interface
test("should make the user retrievable when created", async () => {
  // Given
  const name = "Alice";

  // When
  const user = await createUser({ name });

  // Then
  const retrieved = await getUser(user.id);
  expect(retrieved.name).toBe("Alice");
});
```

**トートロジーなテスト**: 期待値が実装を言い換えたものになっており、構造上必ず通ってしまう。

```typescript
// BAD: Expected value is recomputed the way the code computes it
test("calculateTotal sums line items", () => {
  const items = [{ price: 10 }, { price: 5 }];
  const expected = items.reduce((sum, i) => sum + i.price, 0);
  expect(calculateTotal(items)).toBe(expected);
});

// BAD: The arithmetic is inlined into the assertion — same tautology
test("calculateTotal sums line items", () => {
  const items = [{ price: 10, qty: 3 }, { price: 5, qty: 2 }];
  expect(calculateTotal(items)).toBe(10 * 3 + 5 * 2);
});

// GOOD: Expected value is an independent, known literal
test("should sum the line item prices", () => {
  // Given
  const items = [{ price: 10 }, { price: 5 }];

  // When
  const total = calculateTotal(items);

  // Then
  expect(total).toBe(15);
});
```

**分岐のあるテスト**: テスト本体に条件分岐があり、テスト自身が検証を必要とするコードになっている。

```typescript
// BAD: The test branches — which assertion ran is no longer knowable from the name
test("should price the order", () => {
  // Given
  const order = createOrder({ plan: "pro", seats: 3 });

  // When
  const price = calculatePrice(order);

  // Then
  if (order.plan === "pro") {
    expect(price).toBe(90);
  } else {
    expect(price).toBe(30);
  }
});

// BAD: A ternary in the setup — the condition decides what is being tested
test("should return 401 when the token is missing", async () => {
  // Given
  const token = undefined;
  const headers = token ? { Authorization: token } : {};

  // When
  const response = await get("/me", headers);

  // Then
  expect(response.status).toBe(401);
});

// GOOD: One scenario per test, every value written out
test("should charge 30 per seat when the plan is pro", () => {
  // Given
  const order = createOrder({ plan: "pro", seats: 3 });

  // When
  const price = calculatePrice(order);

  // Then
  expect(price).toBe(90);
});
```

分岐が入ったテストは、通ったときに何が確かめられたのかが名前から読み取れなくなる。条件が誤っていればアサーションは静かに素通りし、テストは緑のまま無を保証する。テストは「それ自体が正しいことを別のテストで証明する必要がないほど自明」でなければならない——だから分岐は、テストではなくケースの分割で表す。

**過剰共有（over-DRY）なテスト**: 結果を左右する値がヘルパーの中に隠れている。

```typescript
// BAD: The value that decides the outcome lives inside the helper
function setupUser() {
  return createUser({ name: "Alice", plan: "free", credits: 0 });
}

test("should reject the export when the user has no credits", async () => {
  const user = setupUser();
  const result = await requestExport(user);
  expect(result.status).toBe("rejected");
});

// GOOD: The builder stays shared, the deciding value is written in the test
test("should reject the export when the user has no credits", async () => {
  // Given
  const user = createUser({ plan: "free", credits: 0 });

  // When
  const result = await requestExport(user);

  // Then
  expect(result.status).toBe("rejected");
});
```

`createUser` のような値のビルダーは共有してよい。テスト本体に戻すべきなのは `credits: 0` ——このテストが通るか落ちるかを決めている値である。

## パラメタライズドテスト

シナリオが同一で、入力と期待値だけが違うとき。各ケースは自分の名前を持ち、その名前も `should ... when ...` で書く。

```typescript
// GOOD: Same scenario throughout, only input and expected value differ
test.each([
  ["should return 401 when the token is missing", {}, 401],
  ["should return 401 when the token is expired", { Authorization: EXPIRED_TOKEN }, 401],
  ["should return 200 when the token has not expired", { Authorization: LIVE_TOKEN }, 200],
])("%s", async (_name, headers, expectedStatus) => {
  // Given

  // When
  const response = await get("/me", headers);

  // Then
  expect(response.status).toBe(expectedStatus);
});
```

ケースごとにセットアップやアサーションが分岐し始めたら、シナリオはもう同一ではない。個別のテストに割ること。
