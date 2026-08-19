"""
spec-driven 基准用例集

覆盖不同难度/形态的需求，用于量化流水线的端到端成功率、覆盖率、契约匹配、耗时与重试轮数。
每个用例给一句可客观判定的自然语言需求；跑 benchmark 时不做人工审阅（spec_review=None）。

注意：这些是「多样性」用例，不是「成功与否」的预设——跑出来的失败同样是有效数据，
用来暴露流水线在哪些需求形态上还站不住。
"""

CASES = [
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


def get_cases(names=None):
    """按名字子集取用例；names=None 返回全部。"""
    if not names:
        return list(CASES)
    wanted = set(names)
    return [c for c in CASES if c["name"] in wanted]
