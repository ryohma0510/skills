# 良いテストと悪いテスト

## 良いテスト

**統合スタイル（integration-style）**: 内部をモックするのではなく、本物のインターフェースを通してテストする。

```typescript
// GOOD: Tests observable behavior
test("user can checkout with valid cart", async () => {
  const cart = createCart();
  cart.add(product);
  const result = await checkout(cart, paymentMethod);
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
test("createUser makes user retrievable", async () => {
  const user = await createUser({ name: "Alice" });
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

// GOOD: Expected value is an independent, known literal
test("calculateTotal sums line items", () => {
  expect(calculateTotal([{ price: 10 }, { price: 5 }])).toBe(15);
});
```
