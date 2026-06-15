# 20 Multi-Step Browser Task Prompts for Navora Lite

这些提示词用于测试多页面浏览任务。每条任务都要求打开至少 3 个页面，覆盖搜索、点击链接、筛选、排序、滚动、跨页面对比、表单填写、返回/继续导航和结构化提取等操作。

安全边界：不要登录账号，不要购买、支付、下单、预约、提交敏感个人信息；商品、旅行和职位任务只提取公开信息；表单任务仅使用公开测试表单。

## No URL Provided

1. 在 Wikipedia 中搜索 `World Wide Web`，打开英文条目并提取摘要和信息框字段；继续打开 `Tim Berners-Lee` 条目提取摘要、出生日期和 known for 字段；再打开页面中指向 `CERN` 的链接，提取 CERN 的摘要和信息框字段，最后返回三页对比摘要。

2. 在 MDN Web Docs 中查找 `Fetch API`，打开文档页提取摘要和主要接口；继续打开文中 `Request` 页面提取用途和常见属性；再打开 `Response` 页面提取用途和常见属性，最后总结 Fetch、Request、Response 的关系。

3. 在 GitHub 中搜索 `playwright browser automation`，筛选 repositories，打开前 3 个仓库详情页，分别提取仓库名、简介、主要语言、star 数、license 和 README 第一段，最后按 star 数排序返回。

4. 在 npm 中搜索 `browser automation`，打开前 3 个包详情页，分别提取包名、版本、周下载量、维护者和 README 摘要，最后对比这些包的主要用途。

5. 在 PyPI 中搜索 `http client`，打开前 3 个 Python 包页面，分别提取包名、最新版本、项目描述、发布日期和项目链接；如果遇到反爬挑战，记录挑战页面标题并停止。

6. 在 Hacker News 首页提取前 5 条文章，按评论数选择评论最多的 3 条，分别打开它们的评论页，提取标题、分数、评论数和前 2 条可见评论摘要。

7. 在 BBC News 中依次进入 World、Technology、Business 三个频道页，分别提取每个频道前 5 条新闻标题、链接和发布时间；最后汇总每个频道的最主要主题。

8. 在 Best Buy 中搜索 `wireless keyboard`，按评分或相关性排序，打开前 3 个商品详情页，分别提取名称、价格、评分、库存状态和主要规格，不要加入购物车。

9. 在 Tripadvisor 中搜索 `Kyoto attractions`，打开前 3 个景点详情页，分别提取名称、评分、评论数、类别、地址或区域和简短描述，最后返回对比表。

10. 在 We Work Remotely 中搜索 `React`，打开前 3 个职位详情页，分别提取职位标题、公司、工作地点或时区、发布日期、薪资信息和申请要求摘要；如果页面要求登录则停止并说明。

## URL Provided

11. 从 `https://en.wikipedia.org/wiki/JavaScript` 开始，提取 JavaScript 的摘要和信息框字段；打开 `Brendan Eich` 链接提取摘要、出生日期和 known for 字段；再打开 `Netscape` 链接提取摘要和信息框字段，最后说明三者关系。

12. 从 `https://developer.mozilla.org/en-US/docs/Web/API` 开始，搜索或打开 `Fetch API`、`Web Storage API`、`Canvas API` 三个文档页，分别提取摘要、主要接口或概念和第一个示例标题。

13. 从 `https://github.com/trending` 开始，打开今日 Trending 前 3 个仓库详情页，分别提取仓库名、简介、README 第一段、主要语言、license 和 star 数，最后按语言分组。

14. 从 `https://www.npmjs.com/` 开始，搜索 `playwright`，打开前 3 个包详情页，分别提取包名、版本、周下载量、维护者和 README 摘要，最后按下载量排序。

15. 从 `https://pypi.org/` 开始，搜索 `fastapi`，打开前 3 个包详情页，分别提取包名、最新版本、描述、发布日期和项目主页链接，最后指出哪个最像官方包。

16. 从 `https://news.ycombinator.com/` 开始，提取首页前 10 条文章，打开评论数最高的 3 条评论页，分别提取标题、分数、评论数和前 2 条可见评论摘要。

17. 从 `https://www.iana.org/domains/reserved` 开始，提取保留域名说明；依次打开页面中提到的 example、invalid、localhost 相关说明页或可访问条目，分别提取用途和保留原因，最后做结构化汇总。

18. 从 `https://httpbin.org/forms/post` 开始，填写公开测试表单中的姓名、电话、邮箱、披萨尺寸、两个 toppings、交付时间和备注，提交后提取回显数据；然后打开 httpbin 的 JSON 示例页和 headers 示例页，分别提取返回内容摘要。

19. 从 `https://www.w3.org/WAI/` 开始，打开首页可见的 3 个主要资源入口，分别提取页面标题、主标题、简介和 3 个关键链接，最后总结这些资源分别适合什么用户。

20. 从 `https://www.timeanddate.com/worldclock/` 开始，依次搜索并打开 Tokyo、New York、London 三个城市页面，分别提取当前时间、时区、天气摘要和 sunrise/sunset 信息，最后按时区差异返回表格。
