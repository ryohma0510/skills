# Glossary — Building Great Skills

何がスキルを優れたものにするかについてのドメインモデル。スキルが存在するのは、確率的なシステムから決定性を絞り出すためであり、根幹の美徳は **Predictability** である。以下の各用語はすべて、それに対するレバーだ。これは [`writing-great-skills`](SKILL.md) のdisclosed referenceである。

用語は軸ごとにグループ化されている：**Invocation**（スキルにどう到達するか）、**Information Hierarchy**（内容がどう構成されるか）、**Steering**（エージェントの実行時の振る舞いがどう形作られるか）、**Pruning**（どうスキルを引き締めた状態に保つか）。各failure modeは、それを治すレバーのそばに置かれ、_failure mode_ とタグ付けされている。

各定義中の**太字の用語**は、この用語集自体の中で定義されている。見出しを頼りに探すこと。

## Predictability

スキルが、実行のたびにエージェントを同じ_やり方_で振る舞わせる度合い——同じ出力ではなく同じプロセス（ブレインストーミング用のスキルは_予測可能に_発散すべきである。トークンは変わっても振る舞いは変わらない）。他のすべての用語が仕える根幹の美徳であり、コストや保守性はこれの症状であって、対立するものではない。

_Avoid_: consistency, reliability, robustness, output-determinism

## Invocation

スキルにどう到達するか——そしてその選択に払う2種類の負荷。

### Model-Invoked

**description** フィールドを保持するスキル。これによりエージェントはそのスキルを見て自律的に発動でき——人間も引き続きその名前をタイプできるので、model-invocationには常にユーザーからの到達可能性が_含まれる_。「モデルのみ」という状態は存在しない。descriptionは常にエージェントの発見可能性を_加える_だけで、人間の到達可能性を取り除くことはない。その発見可能性と引き換えに、毎ターン恒久的な **Context Load** を払う。他のスキルから到達可能でもある——エージェントが発見できるようにするdescriptionは、同時に呼び出し可能にもするからだ。内容がすべて **Reference** であるmodel-invokedスキルは、共有referenceの置き場所にもなる——他のスキルがそれを呼び出せるので、複数のスキルが必要とするreferenceを一箇所にまとめられる。エージェントが自力でスキルに到達しなければならない場合にのみmodel-invocationを選ぶこと。手動でしか発動しないなら、descriptionを外してContext Loadを一切払わないこと。

_Avoid_: ability, tool, capability

### User-Invoked

**description** を取り除いたスキル。エージェントからは見えなくなり、名前をタイプする人間だけが到達できる（ユーザー_のみ_であり、**Model-Invoked** はユーザー_かつ_エージェント）。エージェントによる発見可能性と引き換えに、**Context Load** をゼロにする。descriptionがないため、人間以外は誰も到達できず、他のどのスキルもこれを発動できない。

_Avoid_: procedure, workflow, command

### description

スキルの機械可読なトリガーであり、**Model-Invoked** スキルが常時読み込んでおくことを強いられる唯一の **Context Pointer**。その存在そのものが起動の軸である——保持すればスキルはmodel-invokedになり（他のスキルからも到達可能になり）、削除すれば **User-Invoked** になり、人間だけが到達できるようになる。model-invokedスキルの **Context Load** の発生源。

_Avoid_: frontmatter, summary

### Context Pointer

エージェントのコンテキスト内に保持される参照で、コンテキスト外にある何らかの資料を名指しし、それに到達すべき条件を符号化したもの。**description** は最上位のContext Pointer（コンテキストウィンドウ→スキル）であり、開示されたファイルへのポインタはその1段下にある同種のオブジェクトである。エージェントが_いつ_到達するか——そして_どれだけ確実に_到達するか——を決めるのは、ポインタが指す先ではなくその言い回しである。必須の対象が弱く書かれたポインタの奥にある状態は分散のバグである——まず言い回しを直し、それでも直らない場合にのみ資料をインライン化すること。

_Avoid_: link, reference, import

### Context Load

**Model-Invoked** スキルがエージェントのコンテキストウィンドウに課すコスト——その **description** は常に読み込まれ、トークンと注意の両方を消費する。**User-Invoked** スキルはdescriptionを持たないことでこれを免れる。より多くのmodel-invokedスキルに分割することへのブレーキでもある。

_Avoid_: token cost, context bloat

### Cognitive Load

**User-Invoked** スキルが人間に課すコスト——どのスキルが存在し、いつそれに手を伸ばすべきかを、人間自身が頭の中に保持しなければならない（人間が索引になる）。**Model-Invoked** であることによって、エージェントが発見可能になることで取り除かれるもの。より多くのuser-invokedスキルに分割することへのブレーキでもある。最小化すべきコストではない——それは人間の主体性の対価であり、一部のスキルがuser-invokedのままである理由でもある。人間の判断が重要な場所にはこれを費やし、重要でない場所からは取り除くこと。

_Avoid_: human index, burden, overhead

### Router Skill

他のuser-invokedスキルを指し示すことを役目とする、それ自体もuser-invokedのスキル——それぞれの名前と、いつ手を伸ばすべきかを列挙し、人間が多数ではなく1つのスキルだけを覚えればよいようにする。ヒントを与えることしかできず、発動させることはできない——user-invokedスキルには **description** がないため、人間以外の何もそれらに到達できないからだ。user-invokedスキルが増えたときの **Cognitive Load** に対する治療法。

_Avoid_: dispatcher, menu, registry, index, router procedure

### Granularity

スキルをどれだけ細かく分けるか。細かく分けるほど、2種類の負荷のどちらかを消費する——**Model-Invoked** スキルが増えれば **Context Load** が増す（コンテキストウィンドウに常時載るdescriptionが増え、注意を奪い合う）。**User-Invoked** スキルが増えれば **Cognitive Load** が増す（人間が覚え、手を伸ばすべき対象が増える）。分割は2つの切り口によって導かれる。**Invocation** による分割では、実際にプロンプトで使う独立した **Leading Word** があり、それをトリガーにできる場合にmodel-invokedスキルを切り出す。シーケンスによる分割では、あるStepの **Post-Completion Steps** を隠す必要がある場合に、そのStepを分割する。孤立させることで、後続に隠すべき情報が実際に隠れるからだ。逆方向にも注意すること——シーケンスを統合すると、各Stepの完了後のステップがその後に続くステップに露出してしまい、Premature Completionを招く。

_Avoid_: chunking, modularity

## Information Hierarchy

スキルの内容がどう構成され、はしごのどこまで下に各要素が位置するか。

### Information Hierarchy

スキルの内容を、エージェントがそれをどれだけ即座に必要とするかで順位づけたもの——単一のはしごであり、2つの切り口から生まれる：ファイル内かポインタの奥か、そしてStepかReferenceか。段は次の通り。

- **Steps** —— ファイル内、最優先
- **Reference**（ファイル内）—— 二次的
- **Reference**（開示済み）—— **Context Pointer** の奥

**Steps** を持たないスキルは下2段だけを使う——多くの場合、正当にフラットな並列集合になる（例：レビューのすべてのルールが1つの段に並ぶ）。これは悪い兆候ではなく、妥当な構成である。この階層はinvocationの方式とは独立している——スキルは、すべてStepsであっても、すべてReferenceであっても、両方であっても、model-invokedにもuser-invokedにもなり得る。スキルにStepsがある場合、開示すべきファイル内referenceがそこに埋もれていると、それに注意を払うかどうかがコイントスになってしまう——これは可読性だけでなく分散にも関わるレバーである。はしごの上部は読みやすく保ち、押し下げられるものはすべて押し下げること。

_Avoid_: structure, organization, layout

### Steps

エージェントが実行する順序立ったアクション——スキルがそれを持つ場合、内容の主要な階層であり、`SKILL.md` にその居場所を得る部分。すべてのスキルがStepsを持つわけではない——スキルはすべてSteps（`tdd`）でも、すべて **Reference**（レビュー）でも、その両方でもよく、invocationの方式とは独立している。すべてのStepは **Completion Criterion** ——明確か曖昧かを問わず——で終わる。

_Avoid_: workflow, instructions, choreography

### Reference

エージェントが必要に応じて参照する資料——定義、事実、パラメータ、例、条件付きの指示。スキルに **Steps** がある場合はそれに対して二次的であり、Stepsがない場合はそれが内容のすべてになる。あるいは、どのスキルにも属さずに存在することもある——**External Reference** を参照。**Context Pointer** を通じて到達し、**Progressive Disclosure** の第一候補である。

_Avoid_: supporting material, docs, background

### External Reference

スキルシステムの外に存在する **Reference** ——**description** も **Steps** も持たず、呼び出すこともできない、ただのファイルで、どのスキルからでも指すことができる。それ自体で発動する必要のない共有referenceの置き場所であり、2つの **User-Invoked** スキルが共有できる唯一の場所でもある——どちらもdescriptionを持たないため、互いを呼び出せないからだ。

_Avoid_: doc, resource, knowledge base

### Progressive Disclosure

**Reference** をはしごの下へ動かすこと——`SKILL.md` の外に出し、**Context Pointer** の奥に置くこと——によって、上部を読みやすく保つ。主にトークンの最適化ではなく、**Information Hierarchy** を守るための手段である。**Branch** によって許可される——一部のBranchしか必要としないものを開示し、すべての経路が必要とするものはインラインに置く。ポインタが必須の資料に対して不確実にしか発火しないなら、まずその言い回しを鋭くし、それでも失敗する場合にのみインラインへ引き戻すこと。

_Avoid_: lazy loading, chunking

### Co-location

エージェントが一度に必要とする資料を1箇所にまとめておくこと——ある概念の定義・ルール・注意点を、散らばらせずに1つの見出しの下に置く——ことで、一部を読めば隣接する情報も一緒に読める。**Information Hierarchy** とペアになる、ファイル内での対概念である——階層は_どれだけ下に_あるかを決め、Co-locationはいったんそこに落ち着いたときに_何がその隣にあるか_を決める。referenceの本体の「正しい形式」に決まった公式はない——テストは、スキルがエージェント向けに書かれたドキュメントのように読めるかどうかであり、まとめられた資料はそう読めるが、散らばった資料はそうは読めない。**Duplication** とは別物である——Duplicationは1つの意味を2箇所に繰り返すことであり、散らばりは1つの意味を多数の場所に断片化することである。

_Avoid_: grouping, clustering, cohesion

### Sprawl

_Failure mode._ 単純に長すぎるスキル——`SKILL.md` の行数が多すぎる状態——であり、それが古びているか繰り返されているかとは無関係である。すべての行が生きていて重複がなくてもSprawlはあり得る。可読性（エージェントが行動に移る前により多くをかき分けなければならず、注意が全体に薄まる）、保守性（余分な行1つ1つが **Relevance** を保つべき対象として増える）、トークンの3つを損なう。治療法は **Information Hierarchy** である——**Reference** を **Context Pointer** の奥に開示し、**Branch** やシーケンスで分割して、各経路が必要な分だけを運ぶようにする。**Sediment**（古びた蓄積による長さ）や **Duplication**（繰り返された意味による長さ）とは別物である——Sprawlは原因を問わない、長さそのものである。

_Avoid_: bloat, length, size, verbosity

## Steering

エージェントの実行時の振る舞いを **Predictability** へと形作るレバー。

### Branch

スキルが呼び出されうる異なる方法——スキルが扱う1つのケース——であり、実行のたびに異なる経路をたどる。多くのStepsを持つスキルは多くのBranchを抱えることがあり、線形なスキルにはBranchがない。

_Avoid_: path, case, fork

### Leading Word

_Leitwort_ とも呼ばれる、モデルの事前学習にすでに存在するコンパクトな概念で、エージェントがスキルを実行する間それを使って思考する（例：_lesson_、_proximal zone of development_、_fog of war_、_tracer bullets_）。文として繰り返されるのではなく1つのトークンとして繰り返されることで、スキル全体にわたって分散した定義を蓄積し、振る舞いの領域全体に錨を下ろす。独自の単語を作ることも、明確に定義すれば機能するが、造語は事前学習の恩恵を受けない——事前学習済みの単語がタダで与えてくれるものを、自作語では定義用のトークンで支払うことになる。まず既存の単語に手を伸ばすこと。

Leading Wordは **Predictability** に2重に貢献する。本文中ではその概念が現れるたびにエージェントが同じ振る舞いに手を伸ばすことで_実行_に錨を下ろし、フラットなreferenceの中では注意を1つのクラスの対象に集中させ、毎回正しいチェックを呼び起こす。**description** の中ではそれが_起動_に錨を下ろす——スキル内だけでなく、同じ単語があなたのプロンプト・ドキュメント・コードベースに宿っているとき、エージェントはその共有言語をスキルに結び付け、より確実に発動させる。descriptionには、そのスキルが欲しいときに実際に使うLeading Wordを盛り込むこと。

_Avoid_: keyword, term, motif

### Completion Criterion

エージェントに1つの作業単位が終わったことを伝える条件——エージェントが照らし合わせて判断する目標。単なる品質ではなくレバーであるゆえんは、2つの性質にある。その**明確さ**（エージェントは「完了」と「未完了」を見分けられるか）は **Premature Completion** に抵抗する——曖昧な境界（「理解に達した」）は、エージェントに次のStepへ滑り込む口実を与えてしまう。この軸が効くには_Steps_が必要である。Premature Completionはステップ間の失敗だからだ。その**要求度**（どれだけを求めるか）は **Legwork** を決める——「変更したモデルすべてを確認した」は「変更リストを作る」よりも徹底した作業を強いる——そしてこの軸はStepsに縛られない。フラットなreferenceの本体にも網羅性の基準（「すべてのルールを適用した」）を持たせられ、これがStepsを持たないスキルでも網羅性の基準を持てる理由である。最も強い基準は、チェック可能かつ網羅的の両方を満たす。

_Avoid_: done condition, exit condition, stopping rule

### Legwork

エージェントが1つのStepの内側で、裏側で行う作業——ファイルを読む、コードベースを調べる、変更を加える、ユーザーに丸投げせず自分で必要なものを掘り出すこと。ステップ構造の下に存在し、それ自体が独立したStepとして書かれることは決してなく、言い回しの中に潜み、スキルではなくエージェントによって制御される。**Post-Completion Steps** が持つステップ間での引力に対する、ステップ内での対概念である。**Leading Word**（_comprehensive_、_thorough_）や、作業が網羅的であることを要求する **Completion Criterion** によって高められる——これはフラットなreferenceに適用される要求度の軸も含み、それがフラットなreferenceのスキルにすべての段をカバーさせる原動力になる。その要求が欠けているか、**Premature Completion** がStepを短く切り上げてしまうとき、Legworkは薄くなる。

_Avoid_: scope, effort, diligence, coverage

### Post-Completion Steps

現在のStepに続く **Steps** 群。それが見えていると、エージェントを **Premature Completion** へと前に引っ張る——見えれば見えるほど、その引力は強くなる。防御策は、Stepsの並びを2つに分割して見えないようにすることである。

_Avoid_: horizon, fog of war, lookahead

### Premature Completion

_Failure mode._ 本当に終わる前に現在のStepを終わらせてしまうこと。エージェントの注意が、作業そのものではなく_終わったことにする_方に滑ってしまうために起こる。ステップ間の失敗である——発生するには **Steps** が必要であり、Stepsのないスキルが早々に切り上げるのはPremature Completionではなく、満たされていない要求のもとでの薄い **Legwork** である。2つの力の綱引きである。見えている **Post-Completion Steps**（前へ引っ張る力）と、**Completion Criterion** の明確さ（それに抵抗する力——鋭くチェック可能な基準は持ちこたえ、曖昧な基準は屈する）。曖昧さが必要条件である——鋭い境界は、後続のStepsがどれだけ見えていても引力に抵抗する。だから決して急がないStepは、守る必要すらない。急いでしまうStepには2つのレバーがあるが、この順で試すこと——**まず境界を鋭くする**。これは局所的で安価だからだ。基準が本質的に曖昧で_かつ_実際に急いでいる様子が観測されたときにのみ、**後続のStepsを隠す**——そして隠すことが機能するのは本物のコンテキスト境界を越えたとき（user-invokedでの引き継ぎ、あるいはサブエージェントへのディスパッチ）だけであり、インラインのmodel-invoked呼び出しでは後続のStepsがコンテキストに残ったままで何も解消されない。薄いLegworkの原因の1つではあるが、それとは別物である——Stepが完全に完了してもLegworkは薄いままであり得る。

_Avoid_: premature closure, the rush, rushing, shortcutting

### Negation

_Failure mode._ 禁止によって誘導すること——エージェントに何を_しないか_を伝えること——は裏目に出て、禁じた振る舞いをコンテキストに引きずり込み、かえって意識に上りやすくする。_象のことを考えるな_と言われれば、象がすべてになる。_冗長なコメントを書くな_と言われれば、冗長さこそがエージェントがたった今読んだパターンになる。否定は弱い修飾語であり、強く活性化された概念に押し流されてしまうため、禁止は半ば「それをやれ」という指示として読まれてしまう。そのLeading Wordは_象_である——禁止が何であれフレームの中に名指ししてしまうものだ。治療法：positiveを伝えること——目指す振る舞いを説明する（「1行のコメントを書く」）ことで、禁じたい振る舞いは一度も口にされない。positiveで言い表せない振る舞いに対するハードなガードレールとしてのみ禁止は居場所を得る。その場合でも、必ずpositiveな目標とセットにして、注意が「何をすべきか」に向かうようにすること。

_Avoid_: ironic rebound, don't-prompting, the pink elephant

## Pruning

スキルを引き締まった状態に保つこと——それぞれの治療法は、それが治す失敗とペアになっている。

### Single Source of Truth

各意味がただ1つの権威ある場所に存在する、望ましい状態。そうすることで、スキルの振る舞いへの変更は1箇所への変更で済む。**Duplication** はこれの違反である。

_Avoid_: home, canonical location

### Duplication

_Failure mode._ 同じ意味が複数の **Single Source of Truth** を持ってしまうこと。保守コスト（1箇所を変えたら他も変えなければならない）とトークンを消費し、重要度を膨らませる——ある意味を繰り返すことは、それをはしごの上で実際の順位以上に重く見せてしまう。**Leading Word** の意図せぬ裏返しである——Leading Wordは意味ではなくトークンを繰り返すことで、意図的に注意を高める。

_Avoid_: repetition, redundancy

### Relevance

ある行が今もスキルの動作に関わっているかどうか——何を残すかを判断するレンズ。行がRelevanceを失うのは、そもそもタスクに関わったことがない場合（単なる説明、あるいは開示すべき **Branch**）か、古びてしまった場合（説明対象の振る舞いや世界が変化するにつれてずれていく）である。スキルが短いほどRelevanceを保ちやすい——各行のチェックコストが安くなるからだ。**No-Op** とは別物である——Relevanceはその行がタスクに関わるかどうかを問い、No-Opは振る舞いを変えるかどうかを問う。

_Avoid_: load-bearing, staleness, freshness

### Sediment

_Failure mode._ 追加は安全に感じられ、削除はリスクに感じられるために、スキルの中に積み重なって決して片付けられない古い内容の層——そのため古びた無関係な行が蓄積し、今も生きているものを見つけるにはその層を掘り下げなければならなくなる。刈り込みの規律を持たないスキルがたどる既定の運命であり、**Duplication** の繰り返された意味とは対照的な、**Relevance** のゆっくりとした侵食である。

_Avoid_: accretion, bloat, cruft, rot

### No-Op

_Failure mode._ モデルがデフォルトですでにそれを行うために、何も変えない指示——エージェントがどのみちやることをわざわざ伝えるために負荷を払っていることになる。テストはこうだ——その行はデフォルトと比べて振る舞いを変えるか？ ある行は完全に **Relevance** があってもNo-Opであり得る。**Leading Word** を無料にする同じ事前知識が、No-Opを無価値にする。

Leading Wordは_技法_であり、No-Opはある行に対する_判定_である——そしてこの2つは交差する。デフォルトを上回れないほど弱いLeading Word（エージェントがすでにそこそこ徹底しているときの_be thorough_）はNo-Opであり、修正すべきは別の技法ではなく、その判定を突破できるより強い単語（_relentless_）である。だからNo-Opのテスト——デフォルトと比べて振る舞いを変えるか？——は、Leading Wordがその繰り返しに見合っているかどうかを判定する方法でもある。これはモデル相対的であり、読者相対的ではない——ある行がNo-Opかどうかで2人の意見が割れるとき、それは何がデフォルトかについて意見が割れているのであり、議論ではなくスキルを実際に動かしてみることで決着をつけるべきものである。

_Avoid_: redundant instruction, restating the obvious, belaboring
