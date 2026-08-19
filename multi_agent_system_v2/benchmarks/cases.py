"""
spec-driven 基准用例集

覆盖不同难度/形态的需求，用于量化流水线的端到端成功率、覆盖率、契约匹配、耗时与重试轮数。
每个用例给一句可客观判定的自然语言需求；跑 benchmark 时不做人工审阅（spec_review=None）。

注意：这些是「多样性」用例，不是「成功与否」的预设——跑出来的失败同样是有效数据，
用来暴露流水线在哪些需求形态上还站不住。

两套用例：
- CASES_V1：首轮基线（CRUD / 嵌套 / 校验 / 分页 / 搜索 / 原子自增 / 枚举筛选）。
- CASES_V2：新一轮多样形态（子资源 / 多对多 / PATCH / 聚合 / 库存扣减 / 筛选排序 /
  状态机 / 批量 / 复合唯一键 / 标签+分页），专门压 V1 没覆盖到的边界。
"""

CASES_V1 = [
    {
        "name": "todo_crud",
        "requirement": "开发一个待办事项应用：能新增待办（标题）、列出全部待办、按 id 删除待办；标题为空应返回 422。",
    },
    {
        "name": "auth_register_login",
        "requirement": "开发一个用户系统：注册（用户名+密码，密码至少 8 位，用户名唯一）、登录（用户名+密码，错误返回 401）。",
    },
    {
        "name": "blog_posts_comments",
        "requirement": "开发一个博客系统：创建文章（标题+正文）、列出全部文章、按 id 查看文章、按 id 删除文章、给文章添加评论（评论要有作者+内容）。",
    },
    {
        "name": "product_validation",
        "requirement": "开发一个商品接口：新增商品（名称必填、价格必须大于 0、库存必须是非负整数）、列出全部商品、按 id 查看商品。",
    },
    {
        "name": "paginated_list",
        "requirement": "开发一个分页列表接口：POST 创建条目、GET 列表支持 limit 和 offset 参数、按 id 获取单条、按 id 删除。",
    },
    {
        "name": "order_line_items",
        "requirement": "开发一个订单接口：创建订单（含客户名和多个行项目，每个行项目有商品名和数量）、列出订单、按 id 查看订单。",
    },
    {
        "name": "notes_crud_with_update",
        "requirement": "开发一个笔记应用：创建笔记（标题+内容）、列出、按 id 查看、按 id 更新（PUT 全量）、按 id 删除。",
    },
    {
        "name": "book_library_search",
        "requirement": "开发一个图书接口：新增图书（书名+作者+ISBN）、按书名关键字搜索、列出全部、按 id 查看、按 id 删除。",
    },
    {
        "name": "counter_atomic",
        "requirement": "开发一个计数器接口：POST 创建计数器（名字唯一）、POST 自增、GET 查询当前值、DELETE 删除。",
    },
    {
        "name": "task_priority_filter",
        "requirement": "开发一个任务接口：创建任务（标题+优先级高/中/低）、列出全部、按优先级筛选、标记完成、删除。",
    },
]


CASES_V2 = [
    {
        "name": "user_posts",
        "requirement": "开发一个用户文章系统：创建用户（姓名）、创建文章（标题+正文+所属用户 id）、列出全部文章、按 id 查看文章、列出某用户的全部文章、删除用户；删除用户后该用户的文章也应被删除（按 id 查其文章返回 404）。",
    },
    {
        "name": "course_enrollment",
        "requirement": "开发一个选课系统：创建课程（名称）、创建学生（姓名）、学生选课（课程 id + 学生 id）、列出某课程的全部学生、按 id 查看学生、删除课程；同一学生重复选同一门课应返回 409。",
    },
    {
        "name": "article_patch",
        "requirement": "开发一个文章接口：创建文章（标题+正文+标签列表）、列出全部、按 id 查看文章、按 id 部分更新（PATCH 只改标题，正文保持不变）、按 id 删除。",
    },
    {
        "name": "product_ratings",
        "requirement": "开发一个商品评分接口：创建商品（名称）、给商品提交评分（商品 id + 1 到 5 的整数分）、按 id 查看商品、获取商品的平均分和评分人数。",
    },
    {
        "name": "inventory_order",
        "requirement": "开发一个库存下单系统：创建商品（名称+初始库存，库存非负）、下单扣减库存（商品 id + 数量）、查看商品剩余库存；库存不足时下单返回 409，且库存不得为负。",
    },
    {
        "name": "catalog_filter_sort",
        "requirement": "开发一个商品目录接口：创建商品（名称+分类+价格，价格大于 0）、列出全部商品、按分类筛选、按价格区间筛选（min/max）、按价格升序或降序排列。",
    },
    {
        "name": "ticket_workflow",
        "requirement": "开发一个工单系统：创建工单（标题，状态默认 open）、列出全部、按 id 查看、推进工单状态（open 到 in_progress、in_progress 到 closed）、删除；非法状态跳转（如 open 直接到 closed）返回 422。",
    },
    {
        "name": "bulk_create",
        "requirement": "开发一个批量创建接口：单条创建条目（名称）、批量创建多个条目（一次传多条）、列出全部、按 id 删除；批量创建时任一条目名称为空则整体返回 422 且不创建任何条目。",
    },
    {
        "name": "org_scoped_unique",
        "requirement": "开发一个组织成员系统：创建成员（组织 id + 姓名）、列出全部成员、按 id 删除成员；同一组织内姓名唯一（重复返回 409），不同组织可以有同名成员。",
    },
    {
        "name": "tag_search",
        "requirement": "开发一个带标签的文章接口：创建文章（标题+正文+标签列表）、列出全部、按标签过滤（返回含指定标签的文章）、按标题关键字搜索、分页（limit/offset）。",
    },
]


CASES_BY_SUITE = {"v1": CASES_V1, "v2": CASES_V2}


def get_cases(names=None, suite="v2"):
    """按名字子集取用例；names=None 返回全部。suite 选 v1（首轮基线）或 v2（新一轮多样形态）。"""
    cases = CASES_BY_SUITE.get(suite, CASES_V2)
    if not names:
        return list(cases)
    wanted = set(names)
    return [c for c in cases if c["name"] in wanted]
