# 60 Real Browser Task Prompts for Navora Lite - No URL Version

这些提示词用于测试真实浏览器 Agent。任务覆盖真实网站、真实页面交互和多种复杂度，包括搜索、筛选、排序、点击、滚动、跨页面对比、表单填写、信息提取和结构化汇总。

本版本不在提示词中提供明确 URL，要求浏览器 Agent 根据网站名称、页面名称和任务上下文自行选择入口。

安全边界：不要登录账号，不要购买、支付、下单、预约、提交敏感个人信息，表单任务只填写到提交前或使用公开测试表单。

## Simple

1. 打开 Wikipedia，搜索 `Ada Lovelace`，进入英文条目，提取页面标题、第一段摘要和右侧信息框中的出生日期。

2. 打开 Wikipedia，搜索 `Grace Hopper`，进入英文条目，提取页面标题、第一段摘要和信息框中的 known for 字段。

3. 打开 Hacker News，提取当前首页排名第一的文章标题、来源域名、分数和评论数。

4. 打开 Hacker News，提取首页前 5 条文章的标题和来源域名，按排名返回。

5. 打开 GitHub Trending，提取今日 Trending 页面前 5 个仓库的名称、简介、主要语言和 star 数。

6. 打开 GitHub Trending 的 Python 页面，提取前 5 个 Python Trending 仓库的名称、简介和今日 star 增长数。

7. 打开 MDN Web Docs 的 Fetch API 文档页，提取页面标题、简介段落和前 4 个二级标题。

8. 打开 MDN Web Docs 的 JavaScript 文档页，提取页面标题、简介和页面中可见的 5 个学习入口链接。

9. 打开 IANA 的 reserved domains 页面，提取页面中的保留域名列表，并说明它们为什么被保留。

10. 打开 W3C WAI 首页，提取页面标题、主标题、简介文字和首页可见的 5 个主要导航入口。

11. 打开 timeanddate 的 World Clock 页面，搜索 `Tokyo`，打开对应城市页面，提取当前时间、时区和 sunrise/sunset 信息。

12. 打开 timeanddate 的 World Clock 页面，搜索 `New York`，打开对应城市页面，提取当前时间、时区和天气摘要。

13. 打开 The Weather Channel，搜索 `San Francisco, CA`，进入天气页，提取当前温度、天气状态和今日最高/最低温。

14. 打开 BBC News，提取首页顶部 5 条新闻标题和对应链接。

15. 打开 AP News，提取首页顶部 5 条新闻标题、分类和链接。

16. 打开 Reuters，提取首页可见的 5 条新闻标题和所属频道。

17. 打开 Nike，搜索 `running shoes`，提取搜索结果页前 5 个商品名称和价格，不要加入购物车。

18. 打开 IKEA 美国站，搜索 `desk lamp`，提取前 5 个商品名称、价格和评分信息。

19. 打开 Best Buy，搜索 `wireless mouse`，提取前 5 个商品名称、价格和评分，不要加入购物车。

20. 打开 Target，搜索 `coffee maker`，提取前 5 个商品名称、价格和是否可配送。

## Medium

21. 打开 Amazon 美国站，搜索 `noise cancelling headphones`，提取前 5 个搜索结果的商品名称、价格、评分和 Prime 标识，不要登录、不要加入购物车。

22. 打开 Walmart，搜索 `office chair`，筛选或观察前 5 个结果，提取商品名称、价格、评分和配送/取货信息，不要加入购物车。

23. 打开 Best Buy，搜索 `mechanical keyboard`，把结果按用户评分或相关性排序，提取前 5 个商品名称、价格、评分和库存状态。

24. 打开 IKEA 美国站，搜索 `standing desk`，打开一个商品详情页，提取商品名称、价格、尺寸、颜色选项和是否有库存。

25. 打开 Target，搜索 `air purifier`，打开第一个商品详情页，提取商品名称、价格、评分、主要规格和配送信息。

26. 打开 Nike，搜索 `trail running shoes`，筛选或观察男款/女款结果，提取前 5 个商品名称、价格、颜色数量和是否促销。

27. 打开 Booking，搜索 `Seattle`，入住日期选择下个月第一个周五，退房日期选择两天后，人数 2 人，提取前 5 个住宿名称、评分和价格，不要预订。

28. 打开 Tripadvisor，搜索 `Kyoto restaurants`，提取前 5 个餐厅名称、评分、菜系和价格区间。

29. 打开 Expedia，搜索 `New York hotels`，设置 2 晚、2 位成人，提取前 5 个酒店名称、评分和总价，不要预订。

30. 打开 Google Flights，搜索从 `SFO` 到 `LAX` 的单程航班，日期选择下个月第一个周一，提取前 5 个航班的航空公司、起飞时间、时长和价格，不要购买。

31. 打开 Airbnb，搜索 `Austin`，选择一个周末日期和 2 位客人，提取前 5 个房源标题、评分、每晚价格和区域，不要预订。

32. 打开 Yelp，搜索 `coffee`，地点输入 `San Francisco, CA`，提取前 5 个商家名称、评分、评论数和地址。

33. 打开 LinkedIn Jobs，搜索 `frontend developer`，地点输入 `Remote`，提取前 5 个职位标题、公司和地点；如果要求登录则停止并说明无法继续。

34. 打开 Indeed，搜索 `data analyst`，地点输入 `Remote`，提取前 5 个职位标题、公司、地点和发布时间。

35. 打开 Remote OK，搜索或筛选 `Python`，提取前 8 个远程职位的标题、公司、地点/时区和薪资信息。

36. 打开 We Work Remotely，搜索 `React`，提取前 8 个职位标题、公司、分类和发布日期。

37. 打开 GitHub Search，搜索 `browser automation dashboard`，筛选 repositories，提取前 5 个仓库名称、简介、语言和 star 数。

38. 打开 GitHub Search，搜索 `playwright python agent`，筛选 repositories，提取前 5 个仓库名称、简介、最近更新时间和 star 数。

39. 打开 npm，搜索 `playwright`，提取前 5 个包名、简介、版本和周下载量。

40. 打开 PyPI，搜索 `playwright`，提取前 5 个 Python 包名、简介和最新版本；如果网站出现反爬挑战，则停止并记录挑战页面信息。

## Complex

41. 在 Best Buy 搜索 `wireless mouse`，打开前 3 个商品详情页，分别提取名称、价格、评分、库存状态和主要规格，最后按价格从低到高返回对比表，不要加入购物车。

42. 在 IKEA 美国站搜索 `desk chair`，打开前 3 个结果，提取名称、价格、颜色、尺寸和库存信息，最后推荐最便宜且有库存的选项，不要下单。

43. 在 Target 搜索 `water bottle`，打开前 3 个结果，提取名称、容量、价格、评分和配送状态，最后返回结构化对比结果。

44. 在 Nike 搜索 `running shoes`，打开前 3 个商品详情页，提取名称、价格、可选颜色、尺码提示和评分信息，最后汇总成表格，不要加入购物车。

45. 在 Amazon 美国站搜索 `usb c hub`，打开前 3 个自然搜索结果，提取名称、价格、评分、评论数和关键卖点，最后按评分和价格做简短比较，不要购买。

46. 在 Walmart 搜索 `monitor stand`，打开前 3 个结果，提取名称、价格、评分、配送方式和是否可退货，最后返回对比表。

47. 在 Booking 搜索 `Chicago` 两晚住宿，筛选评分 8+ 或观察高评分结果，打开前 3 个住宿，提取名称、评分、位置、价格和取消政策，不要预订。

48. 在 Tripadvisor 搜索 `San Diego attractions`，打开前 5 个景点结果，提取名称、评分、评论数、类别和简短描述。

49. 在 Yelp 搜索 `brunch`，地点为 `Seattle, WA`，打开前 5 个商家页面，提取名称、评分、评论数、地址、营业状态和价格区间。

50. 在 Google Flights 搜索 `NYC` 到 `MIA` 的往返航班，日期选择下个月第二个周五出发、周日返回，提取前 5 个选项的航空公司、时间、停靠次数和价格，不要购买。

51. 在 GitHub Trending 打开今日 Trending 页面，分别进入前 5 个仓库详情页，提取仓库名称、简介、README 第一段、语言、license 和 star 数。

52. 在 GitHub Search 搜索 `agent browser automation`，筛选 repositories，打开前 5 个仓库，提取名称、简介、star 数、最近提交时间和 README 中的安装方式。

53. 在 npm 搜索 `browser automation`，打开前 5 个包详情页，提取包名、版本、周下载量、维护者和 README 的第一段说明。

54. 在 MDN Web Docs 的 Web API 文档区域中搜索或找到 `Fetch API`、`Web Storage API`、`Canvas API` 三个页面，分别提取页面摘要、主要接口/概念和第一个示例标题。

55. 在英文 Wikipedia 的 Python 编程语言页面提取 Python 的摘要和信息框字段，然后打开 `Guido van Rossum` 链接并提取他的摘要、出生日期和 known for 字段。

56. 在 Wikipedia 搜索 `World Wide Web`，打开英文条目，提取摘要和信息框字段，再打开 `Tim Berners-Lee` 链接并提取他的摘要和 known for 字段。

57. 在 Hacker News 提取前 10 条文章，然后打开评论数最高的一条，提取评论页面标题、分数、评论数和前 3 条可见评论摘要。

58. 在 AP News 打开首页，选择一个新闻分类页，提取该分类页前 8 条新闻标题、发布时间、作者或来源，并返回按时间排序的列表。

59. 在 BBC News 打开首页，进入一个可见的新闻详情页，提取标题、发布时间、作者/来源、正文前 3 段，并返回简短摘要。

60. 打开 httpbin 公开表单测试页，填写姓名、电话、邮箱、披萨尺寸、两个 toppings、交付时间和备注，检查所有字段值正确后提交测试表单，等待响应页并提取回显的表单数据。
