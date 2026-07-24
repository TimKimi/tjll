# 测试用例文档

> 自动生成，请勿手动编辑。重新生成：`python generate_test_docs.py --lang <zh|en>`

## 概览

| 模块 | 数量 |
|---|---|
| 路由 | 82 |
| 服务 | 78 |
| RAG | 77 |
| 数据 | 72 |
| LLM | 68 |
| Schema | 56 |
| 核心 | 28 |
| 模型 | 22 |
| 工具 | 13 |
| **合计** | **496** |

---

## 核心


### test_config

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | resolve_path_absolute | 绝对路径直接返回。 |  | 纯单元 |
| - | repo_root_paths | 基于 REPO_ROOT 拼接的路径。 |  | 纯单元 |
| - | redis_url | 验证Settings对象根据密码、主机、端口和数据库生成正确的redis_url。 |  | 纯单元 |
| - | mineru_pipeline_model_dir_relative | 相对路径时拼接 modelscope_cache_dir。 |  | 纯单元 |
| - | mineru_pipeline_model_dir_absolute | 绝对路径时直接返回。 |  | 纯单元 |
| - | opensearch_url | 验证Settings对象在禁用SSL时生成正确的OpenSearch HTTP URL。 |  | 纯单元 |
| - | opensearch_auth | 验证Settings对象根据用户名和密码生成正确的OpenSearch认证元组。 |  | 纯单元 |
| - | llm_kwargs | 验证Settings对象根据API密钥、基础URL和模型参数生成正确的LLM参数字典。 |  | 纯单元 |

### test_online_tracker

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestOnlineTracker | mark_online_adds_user | mark_online 应记录用户过期时间。 |  | 纯单元 |
| TestOnlineTracker | mark_offline_removes_user | mark_offline 应移除用户记录。 |  | 纯单元 |
| TestOnlineTracker | mark_offline_nonexistent_user | 移除不存在的用户不应报错。 |  | 纯单元 |
| TestOnlineTracker | check_expired_removes_expired | 过期用户应被移除并返回。 |  | 纯单元 |
| TestOnlineTracker | check_expired_no_expired | 没有过期用户时不应执行同步。 |  | 纯单元 |
| TestOnlineTracker | check_expired_calls_sync | 有过期用户时应调 _sync_offline。 | patch | Mock外部API |
| TestOnlineTracker | start_creates_engine_and_resets | start() 应创建引擎并重置所有用户离线。 | patch | Mock外部API |
| TestOnlineTracker | double_start_ignored | 重复 start() 应被忽略。 | patch | Mock外部API |
| TestOnlineTracker | stop_flushes_all | stop() 应清空所有追踪用户。 |  | 纯单元 |
| TestOnlineTracker | flush_all_syncs_remaining | _flush_all 应同步剩余用户。 | patch | Mock外部API |

### test_crud_factory

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestSingletonConfig | json_mode_requires_json_column | data_mode='json' 时必须指定 json_column。 |  | 纯单元 |
| TestSingletonConfig | reset_requires_default_factory | reset=True 时必须提供 default_factory。 |  | 纯单元 |
| TestSingletonConfig | json_mode_with_valid_config | json 模式 + json_column + factory 合法配置。 |  | 纯单元 |
| TestRegisterSingletonRoutes | get_and_put_only | GET + PUT（flat 模式，最常用场景）。 |  | 纯单元 |
| TestRegisterSingletonRoutes | reset_only | 注册 reset 路由。 |  | 纯单元 |
| TestRegisterSingletonRoutes | get_and_delete | GET + DELETE（无 PUT，如只读+删除的场景）。 |  | 纯单元 |
| TestRegisterSingletonRoutes | delete_only | delete=True 且其他全部显式关闭 → 只注册 DELETE。 |  | 纯单元 |
| TestRegisterSingletonRoutes | default_get_true_with_delete | 只设 delete=True 不设 get=False → get=True 仍是默认，同时有 GET 和 DELETE。 |  | 纯单元 |
| TestRegisterSingletonRoutes | json_mode_routes | json 模式注册 GET + PUT + reset。 |  | 纯单元 |
| TestRegisterSingletonRoutes | multiple_calls_no_duplicates | 多次调用产生不同的路由，不能有完全相同的 (path, methods)。 |  | 纯单元 |
---

## 数据


### test_loader

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestMakeAlias | simple_name | 验证_make_alias将简单名称“Garaje”转换为小写别名。 |  | 纯单元 |
| TestMakeAlias | name_with_spaces | 验证_make_alias将带空格的名称转换为短横线连接的别名。 |  | 纯单元 |
| TestMakeAlias | name_with_special_chars | 验证_make_alias移除特殊字符（&和重音）并保留ASCII字母数字。 |  | 纯单元 |
| TestMakeAlias | name_with_unicode | 验证_make_alias在全部非ASCII字符时返回fallback值“unknown”。 |  | 纯单元 |
| TestMakeAlias | strips_whitespace | 验证_make_alias去除首尾空格并将中间空格替换为短横线。 |  | 纯单元 |
| TestMakeAlias | truncates_long_name | 验证_make_alias将超过255字符的长名称截断至255字符以内。 |  | 纯单元 |
| TestParseCategories | single_category | 验证_parse_categories将单个类别解析为包含alias和title的JSON列表。 |  | 纯单元 |
| TestParseCategories | multiple_categories | 验证_parse_categories将多个逗号分隔的类别解析为对应的JSON列表。 |  | 纯单元 |
| TestParseCategories | empty_string_returns_none | 验证_parse_categories对空字符串或纯空格字符串返回None。 |  | 纯单元 |
| TestParseCategories | category_with_special_chars | 处理分类中的 & 和 / 符号。 |  | 纯单元 |
| TestParseCategories | leading_trailing_spaces | 验证_parse_categories处理类别字符串中首尾和中间多余空格。 |  | 纯单元 |
| TestMakeAddress | full_address | 验证_make_address生成包含完整字段（地址、城市、州、邮编、国家、显示地址）的JSON。 |  | 纯单元 |
| TestMakeAddress | minimal_address | 验证_make_address生成仅含基本字段（地址、城市、州、邮编）的最小JSON。 |  | 纯单元 |
| TestParseHours | typical_hours | 验证_parse_hours将星期映射转换为包含营业时段和类型的JSON。 |  | 纯单元 |
| TestParseHours | null_hours_returns_none | 验证_parse_hours对None输入返回None。 |  | 纯单元 |
| TestParseHours | empty_dict_returns_none | 验证_parse_hours对空字典输入返回None。 |  | 纯单元 |
| TestParseHours | closed_day_skipped | '0:0-0:0' 表示当天不营业，应跳过。 |  | 纯单元 |
| TestParseHours | padded_time | 接受 HH:MM 格式（如 10:00）。 |  | 纯单元 |
| TestParseHours | all_days_present | 所有七天都营业时，检查日期映射。 |  | 纯单元 |
| TestParseHours | skip_invalid_day_name | 验证_parse_hours跳过无效的星期名称，只处理有效的键。 |  | 纯单元 |
| TestParseHours | malformed_time_skipped | 验证_parse_hours对格式错误的时间字符串返回None。 |  | 纯单元 |
| TestConvertBusiness | open_business | 验证convert_business将开放商家的原始数据转为标准业务对象。 |  | 纯单元 |
| TestConvertBusiness | closed_business | 验证convert_business将关闭商家（is_open=0）的is_closed设为True。 |  | 纯单元 |
| TestConvertBusiness | no_categories | 验证convert_business在原始数据无分类时将分类设为None。 |  | 纯单元 |
| TestConvertBusiness | no_hours | 验证convert_business在原始数据无营业时间时将时间设为None。 |  | 纯单元 |
| TestConvertReview | typical_review | 验证convert_review将原始评论数据转为标准评论对象（含评分转换）。 |  | 纯单元 |
| TestConvertReview | low_rating | 验证convert_review处理最低评分1.0并正确转换为整数。 |  | 纯单元 |
| TestConvertReview | high_rating | 验证convert_review处理最高评分5.0并正确转换为整数。 |  | 纯单元 |
| TestConvertReview | no_user_id | 极少数情况下 user_id 可能为空。 |  | 纯单元 |

### test_schemas

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestYelpCategory | from_dict | 验证YelpCategory的alias和title属性正确赋值。 |  | 纯单元 |
| TestYelpCoordinates | from_dict | 验证YelpCoordinates的latitude和longitude属性正确赋值。 |  | 纯单元 |
| TestYelpLocation | from_dict_full | 验证YelpLocation完整地址构造包含所有字段和显示地址。 |  | 纯单元 |
| TestYelpLocation | from_dict_minimal | 验证YelpLocation最小构造（仅显示地址）时其他字段为None。 |  | 纯单元 |
| TestYelpBusiness | parse_search_result | 能正确解析 Search 接口返回的商家数据。 |  | 纯单元 |
| TestYelpBusiness | parse_detail_response | 能正确解析 Details 接口返回的额外字段。 |  | 纯单元 |
| TestYelpBusiness | defaults_for_missing_fields | 缺少可选字段时，使用默认值。 |  | 纯单元 |
| TestYelpBusiness | hours_normalized_from_list | hours 字段是 list 时取第一个。 |  | 纯单元 |
| TestYelpBusiness | hours_normalized_from_empty_list | hours 是空 list 时返回 None。 |  | 纯单元 |
| TestYelpBusinessSearchResponse | parse_response | 验证YelpBusinessSearchResponse解析多个商家并正确映射到YelpBusiness列表。 |  | 纯单元 |
| TestYelpReview | parse_review | 验证YelpReview解析包含用户信息的完整评论对象。 |  | 纯单元 |
| TestYelpReview | user_without_image | 验证YelpReview中用户无头像时image_url为None。 |  | 纯单元 |
| TestStoredBusiness | from_yelp | 验证StoredBusiness.from_yelp将YelpBusiness转换为存储格式。 |  | 纯单元 |
| TestStoredReview | from_yelp | 验证StoredReview.from_yelp将YelpReview转换为存储格式并关联商家ID。 |  | 纯单元 |
| TestYelpReviewsResponse | parse_response | 验证YelpReviewsResponse解析多条评论并正确返回YelpReview列表。 |  | 纯单元 |

### test_service

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | get_business | 查询商家。 | asyncio, integration | 集成 |
| - | list_businesses | 商家列表搜索与过滤。 | asyncio, integration | 集成 |
| - | reviews | 评论查询。 | asyncio, integration | 集成 |
| - | biz_with_reviews | 商家及其评论（eager load）。 | asyncio, integration | 集成 |
| - | stats | 数据统计。 | asyncio, integration | 集成 |
| - | rag_interfaces | RAG 使用的批量接口。 | asyncio, integration | 集成 |

### test_user

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestDatasetUser | parse_full | 验证DatasetUser解析包含完整字段（ID、名称、统计、精英年份等）的用户数据。 |  | 纯单元 |
| TestConvertedUser | construct | 验证ConvertedUser构造具有ID、名称、评论数和注册时间的对象。 |  | 纯单元 |
| TestConvertedUser | elite_and_friends_raw_strings | elite 和 friends 存为原始字符串，不应被 JSON 编码。 |  | 纯单元 |
| TestConvertedUser | optional_fields_none | 验证 ConvertedUser 的可选字段 elite 和 friends 默认为 None。 |  | 纯单元 |
| TestConvertUser | typical_conversion | 测试典型 DatasetUser 正确转换为 ConvertedUser，字段值匹配。 |  | 纯单元 |
| TestConvertUser | yelping_since_full_timestamp | yelping_since 接受完整时间戳。 |  | 纯单元 |
| TestConvertUser | empty_elite_friends_become_none | 测试空的 elite 和 friends 字符串在转换后变为 None。 |  | 纯单元 |
| TestConvertUser | long_friends_string | friends 字段可能非常长（数千字符）。 |  | 纯单元 |

### test_yelp_integration

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | search_businesses_real_api | 真实调用 Yelp Search API，验证能返回数据。 | asyncio | 集成 |
| - | get_business_detail_real_api | 真实调用 Details API，验证详细数据。 | asyncio | 集成 |
| - | fetch_and_store_flow | 完整流程测试：搜索 → 获取详情 → 获取评论 → 存库。 | asyncio | 集成 |
| - | reviews_for_known_business | 获取指定商家的评论。 | asyncio | 集成 |

### test_yelp_service

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | yelp_service_init | YelpService 初始化时使用传入的 API key。 | asyncio | 集成 |
| TestYelpServiceMocked | search_businesses | 模拟 Search API 调用，验证解析结果。 | asyncio | 集成 |
| TestYelpServiceMocked | get_business | 模拟 Details API 调用。 | asyncio | 集成 |
| TestYelpServiceMocked | get_reviews | 模拟 Reviews API 调用。 | asyncio | 集成 |
| TestYelpServiceMocked | api_error_raises_yelp_error | API 返回错误时抛出自定义异常。 | asyncio | 集成 |
| TestYelpServiceMocked | api_unauthorized | API Key 无效时返回 401。 | asyncio | 集成 |
| TestYelpServiceMocked | search_with_term_and_categories | 搜索时传 term 和 categories 参数。 | asyncio | 集成 |
| TestYelpServiceMocked | error_without_description_fallback_to_text | 错误 JSON 缺少 description 时 fallback 到 resp.text。 | asyncio | 集成 |
| TestYelpError | construct | 构造 YelpError 并验证状态码、错误码、描述及字符串表示。 |  | 纯单元 |
| TestYelpError | construct_with_unknown | 构造 YelpError 时使用空 code 和 description，仅验证状态码。 |  | 纯单元 |
---

## LLM


### test_client

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | get_llm_passes_settings | 验证 get_llm 将 temperature 和 model 设置传递给 ChatOpenAI。 |  | 纯单元 |
| - | get_llm_with_tools | 测试 get_llm_with_tools 返回的对象包含传入的工具函数。 |  | 纯单元 |

### test_context

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | format_docs | 验证 format_docs 将文档格式化为包含片段序号和内容的字符串。 |  | 纯单元 |

### test_graph_ask

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | route_after_enrich_always_rewrite | 验证 route_after_enrich 无论参数如何都返回 "rewrite"。 |  | 纯单元 |
| - | route_after_attachment | 测试 route_after_attachment 根据 insight_use 和 attachment_filenames 返回路由。 |  | 纯单元 |
| - | route_after_user_insight | 测试 route_after_user_insight 根据 insight_use 返回 fetch_section_insight 或 fetch_user_insight。 |  | 纯单元 |
| - | sources_from_docs_strips_embedding | 验证 sources_from_docs 从文档元数据中移除 embedding 字段。 |  | 纯单元 |
| - | retrieve_writes_sources_to_session_not_state | 验证检索结果写入 session 的 sources，不修改 state。 |  | 纯单元 |
| - | session_pool_lru_flushes_on_evict | 验证会话池在 LRU 淘汰时正确清空历史记录。 |  | 纯单元 |
| - | session_pool_idle_sweep | 验证会话池空闲超时后自动清理过期会话。 |  | 纯单元 |
| - | graph_ask_stream_service | 测试 ask_stream 服务处理先前的对话历史并生成响应。 |  | 纯单元 |
| - | delete_ask_history_and_by_uuid | 验证删除指定 uuid 和 section 的对话历史，以及按 uuid 批量删除。 |  | 纯单元 |
| - | get_section_ids | 测试 get_section_ids 从 uuid 获取对应的 section ID 列表。 |  | 纯单元 |

### test_history

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | get_history_requires_uuid_and_section_id | 验证 get_history 使用 uuid 和 section_id 构造 session_id 和配置。 |  | 纯单元 |
| - | clear_history | 测试 clear_history 清空 uuid 和 section_id 对应的对话历史。 |  | 纯单元 |
| - | clear_histories_for_uuid | 验证 clear_histories_for_uuid 清空指定 uuid 的所有对话历史。 |  | 纯单元 |

### test_insight_persist

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | user_section_redis_roundtrip | 测试 UserInsight 和 SectionInsight 在 Redis 中的保存和加载。 |  | 纯单元 |
| - | registry_restore_and_drop_user_when_last_section | 验证删除最后一个 section 后注册表自动恢复并释放用户 insight。 |  | 纯单元 |
| - | load_section_document_calls_load_file_and_deletes | 验证 load_section_document 调用 load_file 并最终删除临时文件。 |  | 纯单元 |
| - | finalize_syncs_and_saves | 测试 finalize 将对话数据同步并保存到 Redis 和 OpenSearch。 |  | 纯单元 |

### test_interrupt

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | ask_interrupt_persists_questions_via_tool | 验证 ask 中断时通过工具设置中断问题并触发 AskInterruptSignal。 |  | 纯单元 |
| - | submit_applies_result_and_resumes | 测试 submit_ask_interrupt 应用中断答案并继续对话。 |  | 纯单元 |
| - | submit_without_pending_raises | 验证无待处理中断时调用 submit_ask_interrupt 抛出 ValueError。 |  | 纯单元 |
| - | apply_interrupt_answers_replaces_option_with_result | 验证 apply_interrupt_answers 将中断问题选项替换为选中结果。 |  | 纯单元 |

### test_maintain

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | filter_chat_messages_drops_system | 验证 filter_chat_messages 过滤掉 SystemMessage 消息。 |  | 纯单元 |
| - | history_snapshot_user_assistant_only | 验证 history_snapshot 生成仅包含 user 和 assistant 角色的快照。 |  | 纯单元 |
| - | normalize_backend_path_forces_prefix | 验证 normalize_backend_path 为有效路径添加 ./backend/ 前缀。 |  | 纯单元 |
| - | load_history_window_unused_tail_pad_to_3 | 验证 select_history_window 将未使用的尾部补足到至少 3 轮对话。 |  | 纯单元 |
| - | maintain_state_machine_flush_pop_merge | 测试维护状态机正确处理刷新、弹出和合并副本。 |  | 纯单元 |
| - | maintain_keeps_la3_unflushed | batch 与最新 3 轮重叠时：重叠部分不落 Redis、留在内存。 |  | 纯单元 |
| - | get_or_create_consumes_loaded_from_redis | 启动装入内存窗口后，对应消息从 Redis 删除。 |  | 纯单元 |
| - | flush_to_redis_writes_remaining_memory | 释放路径：内存剩余完整轮全部追加 Redis。 |  | 纯单元 |
| - | flush_outside_keep_includes_history_without_pending | keep 窗外 used 轮即使不在 pending（模拟 Redis 装入）也会按序落库。 |  | 纯单元 |
| - | merged_history_redis_plus_memory | get_ask_history 数据源：Redis + 池内内存去重拼接。 |  | 纯单元 |
| - | maintain_active_returns | 验证 maintain 在标记为 active 时直接返回而不处理。 |  | 纯单元 |
| - | insight_facade_get_update | 测试 insight facade 通过服务获取和更新用户及 section 洞察。 |  | 纯单元 |
| - | set_review_truncates_150 | 验证 set_review 将超过 150 字符的评论文本截断。 |  | 纯单元 |
| - | clone_and_merge_replica | 测试克隆 section 洞察副本并在维护后合并变更。 |  | 纯单元 |
| - | release_returns_immediately_and_queues_same_section | 验证 release 立即返回并将同一 section 的维护任务排队。 |  | 纯单元 |
| - | release_other_section_not_blocked | 验证一个 section 的维护不会阻塞其他 section 的 release 操作。 |  | 纯单元 |
| - | release_empty_pool_true | 释放不存在的会话时返回True |  | 纯单元 |
| - | release_maintain_without_seven_gate | 维持不含第七门控的会话池释放逻辑测试 |  | 纯单元 |
| - | get_section_review_falls_back_to_first_memory_query | 获取section review在无本地记录时回退到首次记忆查询 |  | 纯单元 |
| - | occupied_skips_other_section_ask_maintain | 被占用的section在ask维护时跳过其他section |  | 纯单元 |
| - | release_waits_on_occupied | 释放操作等待被占用的会话完成 |  | 纯单元 |
| - | attrs_len_gates_split_and_search | attrs_len属性限制分段和搜索的测试 |  | 纯单元 |

### test_prompts

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | rag_prompt_with_history_formats | RAG带历史记录的提示模板正确格式化消息 |  | 纯单元 |

### test_review_clean_prompts

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | review_clean_prompt_markers | 检查review提示模板中的标记和占位符 |  | 纯单元 |

### test_rewrite

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | has_history_empty | 空历史记录时has_history返回False |  | 纯单元 |
| - | has_history_with_messages | 有消息时has_history返回True |  | 纯单元 |
| - | needs_rewrite_rules | needs_rewrite根据历史、洞察和附件判断是否需要重写 |  | 纯单元 |
| - | rewrite_query_skips_first_turn_empty | 首次轮次无历史时重写查询返回原查询 |  | 纯单元 |
| - | rewrite_query_first_turn_with_insight | 首次轮次有洞察时重写查询包含属性块 |  | 纯单元 |
| - | rewrite_query_first_turn_with_attachment | 首次轮次有附件时重写查询包含文档片段 |  | 纯单元 |
| - | rewrite_query_with_history | 有对话历史时重写查询整合历史信息 |  | 纯单元 |

### test_section_insight

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | section_insight_requires_section_id | 创建SectionInsight时缺少section_id抛出ValueError |  | 纯单元 |
| - | add_facts_append_and_truncate_from_1based | add_facts支持追加和从1-based位置截断替换 |  | 纯单元 |
| - | add_facts_start_invalid | add_facts起始位置为0时抛出异常 |  | 纯单元 |
| - | review_get_set | get_review和set_review正确读写review内容 |  | 纯单元 |
| - | batch_add_section_and_long_text | batch_add_section添加属性并生成section长文本 |  | 纯单元 |
| - | split_and_store_section_mock | 分段存储section洞察数据并验证调用参数 |  | 纯单元 |
| - | search_section_and_documents_delegate | 搜索section属性和文档时委派给存储层函数 |  | 纯单元 |
| - | user_search_skips_when_no_chunks | 无chunk时用户搜索跳过并返回空字符串 |  | 纯单元 |
| - | load_file_pipeline | 加载文件管道正确处理文件、清理和索引 |  | 纯单元 |
| - | llm_tools_callable | LLM工具函数返回正确名称并执行对应操作 |  | 纯单元 |
| - | shared_parent_attrs_across_sections | 不同section共享父级用户洞察属性 |  | 纯单元 |
| - | add_used_filenames_and_delete_unused | 添加文件名并删除未使用文件的逻辑测试 |  | 纯单元 |
| - | delete_disk_files | 删除磁盘文件并返回成功删除的文件列表 |  | 纯单元 |
---

## 模型


### test_app_user

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestAppUserRepr | repr_contains_id_and_username | __repr__ 应包含 id 和 username。 |  | 纯单元 |
| TestAppUserColumns | id_is_primary_key | id 字段应是主键 String(22)。 |  | 纯单元 |
| TestAppUserColumns | username_is_unique_and_indexed | username 字段应是唯一索引。 |  | 纯单元 |
| TestAppUserColumns | password_hash_not_nullable | password_hash 字段不可为空。 |  | 纯单元 |
| TestAppUserColumns | role_column_type_and_default | role 字段应为 String(16)，默认 'user'。 |  | 纯单元 |
| TestAppUserColumns | is_online_column_type_and_default | is_online 字段应为 Boolean，默认 True。 |  | 纯单元 |
| TestAppUserColumns | register_time_has_server_default | register_time 字段应有 server_default。 |  | 纯单元 |
| TestAppUserColumns | optional_string_fields_nullable | bio、avatar 可为空，email 不可为空。 |  | 纯单元 |
| TestAppUserColumns | email_not_nullable | email 字段不可为空。 |  | 纯单元 |
| TestAppUserColumns | email_default_to_empty_string | email 字段默认值为空字符串。 |  | 纯单元 |
| TestAppUserColumns | bio_default_to_empty_string | bio 字段默认值为空字符串。 |  | 纯单元 |
| TestAppUserColumns | avatar_default_to_empty_string | avatar 字段默认值为空字符串。 |  | 纯单元 |
| TestAppUserCreate | create_with_minimal_fields | 仅用必填字段创建用户。 |  | 纯单元 |
| TestAppUserCreate | create_with_all_fields | 使用所有字段创建用户。 |  | 纯单元 |

### test_favorite

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestFavoriteRepr | repr_contains_id_and_shop_id | __repr__ 应包含 id、user_id 和 shop_id。 |  | 纯单元 |
| TestFavoriteColumns | id_is_primary_key | id 字段应是主键 String(22)。 |  | 纯单元 |
| TestFavoriteColumns | user_id_is_foreign_key | user_id 字段应有外键约束。 |  | 纯单元 |
| TestFavoriteColumns | shop_id_is_indexed | shop_id 字段应有索引。 |  | 纯单元 |
| TestFavoriteColumns | created_at_has_server_default | created_at 字段应有 server_default。 |  | 纯单元 |
| TestFavoriteColumns | user_id_ondelete_cascade | user_id 的外键应配置 CASCADE 删除。 |  | 纯单元 |
| TestFavoriteCreate | create_with_minimal_fields | 仅用必填字段创建收藏记录。 |  | 纯单元 |
| TestFavoriteCreate | create_with_all_fields | 使用所有字段创建收藏记录。 |  | 纯单元 |
---

## RAG


### test_document_chunking

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | split_text_to_chunks_with_explicit_size | 指定chunk_size和overlap时正确分段文本 |  | 纯单元 |
| - | split_text_to_chunks_short_text_single_chunk | 短文本只返回一个chunk |  | 纯单元 |

### test_document_clean

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | clean_text_empty | 空字符串清洗后仍为空 |  | 纯单元 |
| - | clean_text_strips_null_bytes | 清洗去除null字节 |  | 纯单元 |
| - | clean_text_normalizes_newlines_and_spaces | 清洗标准化换行和空格 |  | 纯单元 |
| - | normalize_jsonish_dict_and_list | normalize_jsonish压缩字典和列表为紧凑JSON |  | 纯单元 |
| - | normalize_jsonish_escaped_string | normalize_jsonish处理转义字符串去掉空格 |  | 纯单元 |
| - | normalize_jsonish_invalid_keeps_strip | 非法JSON输入仅strip返回 |  | 纯单元 |
| - | normalize_jsonish_none | None输入返回None |  | 纯单元 |

### test_document_embed_pdf

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | resolve_embedding_device_cpu | resolve_embedding_device处理cpu参数 |  | 纯单元 |
| - | resolve_embedding_device_cuda_fallback | cuda不可用回退为cpu |  | 纯单元 |
| - | resolve_embedding_device_cuda_ok | cuda可用时返回cuda |  | 纯单元 |
| - | resolve_embedding_device_import_error | *test_resolve_embedding_device_import_error* |  | 纯单元 |
| - | embed_chunks_and_query | *test_embed_chunks_and_query* |  | 纯单元 |
| - | parse_pdf_with_mineru_mocked | *test_parse_pdf_with_mineru_mocked* |  | 纯单元 |
| - | parse_pdf_import_error | *test_parse_pdf_import_error* |  | 纯单元 |

### test_document_indexing

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | make_chunk_id_format_and_stable | *test_make_chunk_id_format_and_stable* |  | 纯单元 |
| - | build_yelp_chunk_docs_polarity_and_last_flag | *test_build_yelp_chunk_docs_polarity_and_last_flag* |  | 纯单元 |
| - | normalize_business_fields_jsonish | *test_normalize_business_fields_jsonish* |  | 纯单元 |
| - | index_chunks_to_opensearch | *test_index_chunks_to_opensearch* |  | 纯单元 |
| - | index_business_summaries_splits_polarities | 好评/坏评分开切分，分两次 bulk，不跨侧拼接。 |  | 纯单元 |
| - | index_business_pos_error_skips_neg | *test_index_business_pos_error_skips_neg* |  | 纯单元 |
| - | index_business_neg_error_after_pos | *test_index_business_neg_error_after_pos* |  | 纯单元 |
| - | index_business_empty_summaries | *test_index_business_empty_summaries* |  | 纯单元 |

### test_document_loaders

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | load_md_file | *test_load_md_file* |  | 纯单元 |
| - | load_txt_file | *test_load_txt_file* |  | 纯单元 |
| - | load_missing_file_raises | *test_load_missing_file_raises* |  | 纯单元 |
| - | load_unsupported_extension | *test_load_unsupported_extension* |  | 纯单元 |
| - | load_pdf_uses_mineru | *test_load_pdf_uses_mineru* |  | 纯单元 |
| - | load_docx | *test_load_docx* |  | 纯单元 |
| - | load_image_uses_mineru | *test_load_image_uses_mineru* |  | 纯单元 |
| - | image_to_single_page_pdf | *test_image_to_single_page_pdf* |  | 纯单元 |

### test_index_cleaned_yelp

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | run_index_missing_dir | *test_run_index_missing_dir* |  | 纯单元 |
| - | backfill_skips_already_and_marks_complete | *test_backfill_skips_already_and_marks_complete* |  | 纯单元 |
| - | backfill_does_not_mark_incomplete | *test_backfill_does_not_mark_incomplete* |  | 纯单元 |
| - | rewrite_clears_progress_and_reindexes_all | *test_rewrite_clears_progress_and_reindexes_all* |  | 纯单元 |
| - | main_rewrite_recreate_and_limit | *test_main_rewrite_recreate_and_limit* |  | 纯单元 |
| - | run_index_returns_1_on_bulk_errors | *test_run_index_returns_1_on_bulk_errors* |  | 纯单元 |

### test_index_progress

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | list_business_json_excludes_progress | *test_list_business_json_excludes_progress* |  | 纯单元 |
| - | progress_path_and_roundtrip | *test_progress_path_and_roundtrip* |  | 纯单元 |
| - | load_progress_invalid_completed | *test_load_progress_invalid_completed* |  | 纯单元 |
| - | both_sides_fully_indexed | *test_both_sides_fully_indexed* |  | 纯单元 |

### test_opensearch_client

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | get_opensearch_client_uses_settings | *test_get_opensearch_client_uses_settings* |  | 纯单元 |

### test_opensearch_schema

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | index_mapping_body_structure | *test_index_mapping_body_structure* |  | 纯单元 |
| - | hybrid_pipeline_body_weights | *test_hybrid_pipeline_body_weights* |  | 纯单元 |
| - | ensure_search_pipeline | *test_ensure_search_pipeline* |  | 纯单元 |
| - | ensure_index_create_and_recreate | *test_ensure_index_create_and_recreate* |  | 纯单元 |

### test_retrieve_rerank

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | rerank_docs_empty | *test_rerank_docs_empty* |  | 纯单元 |
| - | rerank_docs_orders_by_score | *test_rerank_docs_orders_by_score* |  | 纯单元 |
| - | rerank_docs_single_float_score | *test_rerank_docs_single_float_score* |  | 纯单元 |

### test_retrieve_search

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | format_hits_and_hits_to_documents | *test_format_hits_and_hits_to_documents* |  | 纯单元 |
| - | hits_to_documents_includes_yelp_meta | *test_hits_to_documents_includes_yelp_meta* |  | 纯单元 |
| - | retriever_tolerates_missing_source_file | Yelp chunk 无 source_file，Retriever 不得 KeyError。 |  | 纯单元 |
| - | source_excludes_embedding_only | *test_source_excludes_embedding_only* |  | 纯单元 |
| - | vector_bm25_hybrid_search | *test_vector_bm25_hybrid_search* |  | 纯单元 |
| - | get_retriever_and_modes | *test_get_retriever_and_modes* |  | 纯单元 |

### test_review_clean_batching

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | filter_short_reviews | *test_filter_short_reviews* |  | 纯单元 |
| - | pack_by_char_budget_basic | *test_pack_by_char_budget_basic* |  | 纯单元 |
| - | pack_by_char_budget_empty | *test_pack_by_char_budget_empty* |  | 纯单元 |
| - | pack_by_char_budget_too_small | *test_pack_by_char_budget_too_small* |  | 纯单元 |
| - | pack_truncates_oversized_item | *test_pack_truncates_oversized_item* |  | 纯单元 |

### test_review_clean_llama_client

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | chat_uses_http_when_already_started | *test_chat_uses_http_when_already_started* |  | 纯单元 |
| - | stop_noop_when_not_started | *test_stop_noop_when_not_started* |  | 纯单元 |

### test_review_clean_pipeline

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | input_char_budget | *test_input_char_budget* |  | 纯单元 |
| - | parse_extract_deltas | *test_parse_extract_deltas* |  | 纯单元 |
| - | star_needs | *test_star_needs* |  | 纯单元 |
| - | append_delta_and_trim | *test_append_delta_and_trim* |  | 纯单元 |
| - | clean_business_no_reviews | *test_clean_business_no_reviews* |  | 纯单元 |
| - | clean_business_happy_path | *test_clean_business_happy_path* |  | 纯单元 |
| - | load_clean_config_missing | *test_load_clean_config_missing* |  | 纯单元 |

### test_review_clean_shard

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | stable_shard_deterministic | *test_stable_shard_deterministic* |  | 纯单元 |
| - | filter_shard_ids | *test_filter_shard_ids* |  | 纯单元 |
| - | slice_ids | *test_slice_ids* |  | 纯单元 |
| - | progress_roundtrip | *test_progress_roundtrip* |  | 纯单元 |

### test_section_indexing

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| - | make_section_document_chunk_id_stable | *test_make_section_document_chunk_id_stable* |  | 纯单元 |
| - | section_insight_mapping_has_section_id | *test_section_insight_mapping_has_section_id* |  | 纯单元 |
| - | build_section_document_chunk_docs | *test_build_section_document_chunk_docs* |  | 纯单元 |
---

## 路由


### test_admin

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestAdminRoutes | get_admin_profile_success | 获取管理员信息成功。 | patch | Mock外部API |
| TestAdminRoutes | get_admin_profile_not_admin | 非管理员请求应返回 403。 | patch | Mock外部API |
| TestAdminRoutes | list_users_empty | 空用户列表。 | patch | Mock外部API |
| TestAdminRoutes | list_users_with_items | 用户列表包含项。 | patch | Mock外部API |
| TestAdminRoutes | list_users_requires_auth | 未认证请求应返回 401。 | patch | Mock外部API |
| TestAdminRoutes | update_role_success | 修改用户角色成功。 | patch | Mock外部API |
| TestAdminRoutes | update_role_not_admin | 非管理员修改角色应返回 403。 | patch | Mock外部API |
| TestAdminRoutes | delete_user_success | 删除用户成功。 | patch | Mock外部API |
| TestAdminRoutes | delete_user_not_admin | 非管理员删除用户应返回 403。 | patch | Mock外部API |

### test_ai_routes

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestAiAskRoute | ask_returns_interrupt | ask 返回 AskInterruptResult 时应返回问卷 JSON。 | patch | Mock外部API |
| TestAiAskRoute | ask_streaming | ask 返回 AskStream 时应返回流式响应。 | patch | Mock外部API |
| TestAiAskRoute | ask_non_stream | ask 非流式应返回 JSON。 | patch | Mock外部API |
| TestAiAskRoute | ask_non_stream_no_response | 非流式且 response 为 None 时应返回 500。 | patch | Mock外部API |
| TestAiAskRoute | ask_requires_auth | 未认证请求返回 401。 |  | 纯单元 |
| TestAiAskInterruptRoute | submit_interrupt_returns_stream | 提交澄清答案应返回流式响应。 | patch | Mock外部API |
| TestAiAskInterruptRoute | submit_interrupt_requires_auth | 未认证请求返回 401。 |  | 纯单元 |

### test_auth

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestAuthRoutes | register_success | 注册成功应返回 201 + token。 | patch | Mock外部API |
| TestAuthRoutes | register_duplicate | 重复用户名应返回 409。 | patch | Mock外部API |
| TestAuthRoutes | login_success | 登录成功应返回 200 + token。 | patch | Mock外部API |
| TestAuthRoutes | login_wrong_password | 密码错误应返回 401。 | patch | Mock外部API |
| TestAuthRoutes | logout_success | 退出登录应返回 200。 | patch | Mock外部API |
| TestAuthRoutes | admin_login_success | 管理员登录。 | patch | Mock外部API |
| TestAuthRoutes | forgot_password_success | 忘记密码应返回 200（无论邮箱是否存在）。 | patch | Mock外部API |
| TestAuthRoutes | reset_password_success | 重置密码成功。 | patch | Mock外部API |
| TestAuthRoutes | reset_password_invalid_token | 无效的重置令牌应返回 400。 | patch | Mock外部API |

### test_avatar

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestAvatarRoutes | upload_avatar_success | 上传头像成功应返回 200 + 头像 URL。 | patch | Mock外部API |
| TestAvatarRoutes | upload_avatar_invalid_type | 不支持的图片格式应返回 400。 | patch | Mock外部API |
| TestAvatarRoutes | upload_avatar_too_large | 文件超过大小限制应返回 400。 | patch | Mock外部API |
| TestAvatarRoutes | upload_avatar_requires_auth | 未认证请求应返回 401。 |  | 纯单元 |
| TestAvatarCompression | compress_large_jpeg | 超过 512px 的大图应被缩放到 ≤512px。 |  | 纯单元 |
| TestAvatarCompression | compress_small_image_unchanged_dimensions | 小于 512px 的小图不应被放大。 |  | 纯单元 |
| TestAvatarCompression | compress_rgba_png | RGBA PNG 应被转为 RGB 保存。 |  | 纯单元 |
| TestAvatarCompression | compress_invalid_data_raises_error | 损坏的图片数据应抛出友好的 AppError。 |  | 纯单元 |
| TestAvatarCompression | compress_save_failure_raises_error | 能解码但无法重编码的图片应抛出友好错误。 |  | 纯单元 |
| TestAvatarCompression | compress_result_smaller_than_original | 压缩后的文件大小应小于原始文件。 |  | 纯单元 |

### test_business

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestBusinessRoutes | list_businesses | *test_list_businesses* | patch | Mock外部API |
| TestBusinessRoutes | list_businesses_defaults | *test_list_businesses_defaults* | patch | Mock外部API |
| TestBusinessRoutes | list_businesses_with_yelp_source | *test_list_businesses_with_yelp_source* | patch | Mock外部API |
| TestBusinessRoutes | business_detail_found | *test_business_detail_found* | patch | Mock外部API |
| TestBusinessRoutes | business_detail_not_found | *test_business_detail_not_found* | patch | Mock外部API |

### test_favorite

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestFavoriteRoutes | list_favorites_empty | 空收藏列表应返回空列表。 | patch | Mock外部API |
| TestFavoriteRoutes | list_favorites_with_items | 收藏列表应返回收藏项。 | patch | Mock外部API |
| TestFavoriteRoutes | list_favorites_requires_auth | 未认证请求应返回 401。 | patch | Mock外部API |
| TestFavoriteRoutes | add_favorite_success | 添加收藏成功。 | patch | Mock外部API |
| TestFavoriteRoutes | add_favorite_duplicate | 重复收藏应返回 409。 | patch | Mock外部API |
| TestFavoriteRoutes | add_favorite_shop_not_found | 商家不存在应返回 404。 | patch | Mock外部API |
| TestFavoriteRoutes | remove_favorite_success | 移除收藏成功。 | patch | Mock外部API |
| TestFavoriteRoutes | remove_favorite_not_found | 收藏不存在应返回 404。 | patch | Mock外部API |

### test_file_upload

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestFileUploadRoutes | upload_success | 上传成功应返回文件信息。 | patch | Mock外部API |
| TestFileUploadRoutes | upload_requires_auth | 未认证请求返回 401。 | patch | Mock外部API |
| TestFileUploadRoutes | upload_response_schema | FileUploadResponse 序列化正确。 |  | 纯单元 |

### test_health

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestHealthRoutes | health_check | /health 接口返回正确的状态和数据。 |  | 纯单元 |
| TestHealthRoutes | health_check_method_not_allowed | 非 GET 方法返回 405。 |  | 纯单元 |
| TestHealthRoutes | health_check_response_headers | 响应头。 |  | 纯单元 |

### test_review

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestReviewRoutes | list_reviews | *test_list_reviews* | patch | Mock外部API |
| TestReviewRoutes | list_reviews_with_default_params | *test_list_reviews_with_default_params* | patch | Mock外部API |
| TestReviewRoutes | list_reviews_with_yelp_source | *test_list_reviews_with_yelp_source* | patch | Mock外部API |
| TestReviewRoutes | review_detail_found | *test_review_detail_found* | patch | Mock外部API |
| TestReviewRoutes | review_detail_not_found | *test_review_detail_not_found* | patch | Mock外部API |
| TestReviewRoutes | list_reviews_invalid_sort | *test_list_reviews_invalid_sort* | patch | Mock外部API |

### test_user

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestUserRoutes | get_profile | 获取用户信息。 |  | 纯单元 |
| TestUserRoutes | get_profile_not_found | 用户不存在。 |  | 纯单元 |
| TestUserRoutes | update_profile | 更新用户信息。 |  | 纯单元 |
| TestUserRoutes | get_settings_defaults | 设置无记录时返回默认值。 |  | 纯单元 |
| TestUserRoutes | get_settings | 获取已有设置。 |  | 纯单元 |
| TestUserRoutes | update_settings | 更新设置（已有记录）。 |  | 纯单元 |
| TestUserRoutes | update_settings_create_new | 更新设置（无记录→新建）。 |  | 纯单元 |
| TestUserRoutes | reset_settings | 重置设置为默认值。 |  | 纯单元 |
| TestUserRoutes | reset_settings_create_new | 重置设置（无记录→新建）。 |  | 纯单元 |
| TestUserRoutes | delete_account | 注销账号成功。 |  | 纯单元 |
| TestUserRoutes | delete_account_not_found | 用户不存在时返回 404。 |  | 纯单元 |
| TestUserRoutes | delete_account_requires_auth | 未认证请求返回 401。 |  | 纯单元 |
| TestCleanupUserResources | avatar_file_deleted | 用户有头像时删除头像文件。 | asyncio | Mock服务 |
| TestCleanupUserResources | avatar_file_not_exists | 头像文件已不存在时不报错。 | asyncio | Mock服务 |
| TestCleanupUserResources | no_avatar_skips_file_deletion | 用户无头像时不执行文件删除（但附件目录仍会处理）。 | asyncio | Mock服务 |
| TestCleanupUserResources | user_file_dir_deleted | 有用户名时删除附件目录。 | asyncio | Mock服务 |
| TestCleanupUserResources | no_username_skips_dir_deletion | 用户无用户名时跳过附件目录删除（但头像仍会处理）。 | asyncio | Mock服务 |
| TestCleanupUserResources | oserror_logged_not_raised | 文件删除失败只打 warning，不抛异常。 | asyncio | Mock服务 |
| TestUserInsightRoutes | get_insight | 获取用户画像成功。 | patch | Mock外部API |
| TestUserInsightRoutes | update_insight | 更新用户画像成功。 | patch | Mock外部API |
| TestUserInsightRoutes | delete_insight | 删除用户画像成功。 | patch | Mock外部API |
| TestUserInsightRoutes | delete_all_insights | 删除所有画像成功。 | patch | Mock外部API |
---

## Schema


### test_auth

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestRegisterRequest | valid | 合法注册请求。 |  | 纯单元 |
| TestRegisterRequest | email_required | 邮箱是必填字段。 |  | 纯单元 |
| TestRegisterRequest | email_invalid_format | 邮箱格式不正确应报错。 |  | 纯单元 |
| TestRegisterRequest | username_too_short | 用户名少于 2 位应报错。 |  | 纯单元 |
| TestRegisterRequest | username_too_long | 用户名超过 16 位应报错。 |  | 纯单元 |
| TestRegisterRequest | password_too_short | 密码少于 8 位应报错。 |  | 纯单元 |
| TestLoginRequest | valid_minimal | *test_valid_minimal* |  | 纯单元 |
| TestLoginRequest | valid_with_remember | *test_valid_with_remember* |  | 纯单元 |
| TestLoginRequest | blank_username | *test_blank_username* |  | 纯单元 |
| TestTokenResponse | valid | *test_valid* |  | 纯单元 |
| TestTokenResponse | token_cannot_be_empty | *test_token_cannot_be_empty* |  | 纯单元 |
| TestUserInfo | valid_minimal | *test_valid_minimal* |  | 纯单元 |
| TestUserInfo | valid_full | 验证UserInfo完整字段赋值及角色字符串转换正确 |  | 纯单元 |
| TestUserInfo | role_default | 验证UserInfo角色默认值为UserRole.USER |  | 纯单元 |
| TestUserInfo | invalid_role | role 只能是 user 或 admin。 |  | 纯单元 |
| TestRefreshTokenRequest | valid | 验证RefreshTokenRequest正确存储refresh_token |  | 纯单元 |
| TestRefreshTokenRequest | empty_token | 验证空refresh_token触发ValidationError |  | 纯单元 |

### test_common

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestApiResponse | ok_without_data | 验证ApiResponse.ok无数据时返回code 200和message "success" |  | 纯单元 |
| TestApiResponse | ok_with_data | 验证ApiResponse.ok带数据时正确返回data |  | 纯单元 |
| TestApiResponse | ok_with_custom_message | 验证ApiResponse.ok支持自定义message |  | 纯单元 |
| TestApiResponse | fail_default | 验证ApiResponse.fail默认返回code 400和message "error" |  | 纯单元 |
| TestApiResponse | fail_custom | 验证ApiResponse.fail自定义code和message |  | 纯单元 |
| TestApiResponse | direct_instantiation | 验证ApiResponse直接实例化自定义code、message和data |  | 纯单元 |
| TestApiResponse | generic_with_different_types | 验证ApiResponse.ok支持不同data类型（list和string） |  | 纯单元 |
| TestPaginationParams | defaults | 验证PaginationParams默认page为1、page_size为10 |  | 纯单元 |
| TestPaginationParams | valid_values | 验证PaginationParams自定义page和page_size |  | 纯单元 |
| TestPaginationParams | page_ge_1 | 验证page为0时触发ValidationError |  | 纯单元 |
| TestPaginationParams | page_size_ge_1 | 验证page_size为0时触发ValidationError |  | 纯单元 |
| TestPaginationParams | page_size_le_100 | 验证page_size为101时触发ValidationError |  | 纯单元 |
| TestPaginationParams | page_size_boundary_values | 验证page_size边界值1和100正常 |  | 纯单元 |
| TestPaginatedData | instantiation | 验证PaginatedData完整实例化及字段值 |  | 纯单元 |
| TestPaginatedData | with_string_items | 验证PaginatedData支持字符串类型items |  | 纯单元 |
| TestPaginatedData | with_complex_objects | 验证PaginatedData支持复杂对象items |  | 纯单元 |
| TestPaginatedData | empty_items | 验证PaginatedData空items时total和total_pages为0 |  | 纯单元 |

### test_favorite

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestAddFavoriteRequest | valid | 合法请求。 |  | 纯单元 |
| TestAddFavoriteRequest | shop_id_required | shop_id 是必填字段。 |  | 纯单元 |
| TestAddFavoriteRequest | shop_id_cannot_be_empty | shop_id 不能为空字符串。 |  | 纯单元 |
| TestFavoriteItem | valid_minimal | 仅用必填字段创建。 |  | 纯单元 |
| TestFavoriteItem | valid_full | 使用所有字段创建。 |  | 纯单元 |
| TestFavoriteItem | id_required | id 是必填字段。 |  | 纯单元 |
| TestFavoriteItem | shop_id_required | shop_id 是必填字段。 |  | 纯单元 |
| TestFavoriteItem | created_at_required | created_at 是必填字段。 |  | 纯单元 |

### test_user

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestUserProfileResponse | valid_minimal | 验证UserProfileResponse最小字段及默认值 |  | 纯单元 |
| TestUserProfileResponse | valid_full | 验证UserProfileResponse完整字段赋值 |  | 纯单元 |
| TestUpdateProfileRequest | all_fields_optional | 全部字段选填。 |  | 纯单元 |
| TestUpdateProfileRequest | partial_update | 只更新部分字段。 |  | 纯单元 |
| TestUpdateProfileRequest | email_validation | 邮箱格式不正确应报错。 |  | 纯单元 |
| TestUpdateProfileRequest | valid_email | 验证UpdateProfileRequest设置email字段 |  | 纯单元 |
| TestUpdateProfileRequest | bio_too_long | bio 超过 500 字应报错。 |  | 纯单元 |
| TestUpdateProfileRequest | bio_boundary | 验证UpdateProfileRequest的bio字段500字符边界 |  | 纯单元 |

### test_user_setting

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestUserSettingResponse | minimal | 验证UserSettingResponse默认值全为空 |  | 纯单元 |
| TestUserSettingResponse | with_values | 验证UserSettingResponse带值实例化 |  | 纯单元 |
| TestUserSettingResponse | extra_fields_ignored | 验证UserSettingResponse未知字段被忽略 |  | 纯单元 |
| TestUserSettingUpdateRequest | all_optional | 验证UserSettingUpdateRequest所有字段可选且默认None |  | 纯单元 |
| TestUserSettingUpdateRequest | partial_update | 验证UserSettingUpdateRequest部分更新不影响其他字段 |  | 纯单元 |
| TestUserSettingUpdateRequest | extra_fields_ignored | 验证UserSettingUpdateRequest未知字段被忽略 |  | 纯单元 |
---

## 服务


### test_admin

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestChangeRole | change_role_success | 管理员可将用户角色从 user 改为 admin。 | asyncio | Mock服务 |
| TestChangeRole | change_role_self_not_allowed | 管理员不能修改自己的角色。 | asyncio | Mock服务 |
| TestChangeRole | change_role_user_not_found | 不存在的用户应抛出异常。 | asyncio | Mock服务 |
| TestDeleteUser | delete_user_success | 管理员可删除其他用户。 | asyncio | Mock服务 |
| TestDeleteUser | delete_user_self_not_allowed | 管理员不能删除自己的账号。 | asyncio | Mock服务 |
| TestDeleteUser | delete_user_not_found | 不存在的用户应抛出异常。 | asyncio | Mock服务 |

### test_auth

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestRegister | register_creates_user | 注册成功应返回用户信息和 token。 | asyncio | Mock服务 |
| TestRegister | register_duplicate_username | 重复用户名应抛出异常。 | asyncio | Mock服务 |
| TestRegister | register_password_is_hashed | 注册时密码应被哈希存储。 | asyncio | Mock服务 |
| TestRegister | register_with_email | 注册时可附带邮箱。 | asyncio | Mock服务 |
| TestLogin | login_success | 正确的用户名密码应返回 token。 | asyncio | Mock服务 |
| TestLogin | login_wrong_password | 密码错误应抛出异常。 | asyncio | Mock服务 |
| TestLogin | login_user_not_found | 用户不存在应抛出异常。 | asyncio | Mock服务 |
| TestLogin | login_updates_is_online | 登录成功后应标记用户在线。 | asyncio | Mock服务 |
| TestLogout | logout_marks_user_offline | 退出应标记用户离线。 | asyncio | Mock服务 |
| TestLogout | logout_user_not_found | 不存在的用户退出应不报错。 | asyncio | Mock服务 |
| TestForgotPassword | forgot_password_existing_user | 存在的邮箱应发送重置邮件（不抛出异常）。 | asyncio | Mock服务 |
| TestForgotPassword | forgot_password_nonexistent_email | 不存在的邮箱不应抛出异常（防止枚举）。 | asyncio | Mock服务 |
| TestResetPassword | reset_password_success | 有效的密钥 + 匹配的哈希 → 重置成功。 | asyncio | Mock服务 |
| TestResetPassword | reset_password_with_formatting | 带短横线和大写的格式化密钥也应能正常解析。 | asyncio | Mock服务 |
| TestResetPassword | reset_password_invalid_token | 数据库中不存在的密钥应拒绝。 | asyncio | Mock服务 |
| TestResetPassword | reset_password_expired_token | 过期的密钥应拒绝并清除。 | asyncio | Mock服务 |

### test_business

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestHelpers | parse_json_field_valid | 验证_parse_json_field解析有效JSON字符串为字典 |  | 纯单元 |
| TestHelpers | parse_json_field_none | 验证_parse_json_field输入None返回None |  | 纯单元 |
| TestHelpers | parse_json_field_invalid | 验证_parse_json_field输入无效字符串返回None |  | 纯单元 |
| TestHelpers | parse_json_list_valid | 验证_parse_json_list解析有效JSON列表 |  | 纯单元 |
| TestHelpers | parse_json_list_none | 验证_parse_json_list输入None返回空列表 |  | 纯单元 |
| TestHelpers | parse_json_list_invalid | 验证_parse_json_list输入无效JSON返回空列表 |  | 纯单元 |
| TestHelpers | parse_json_list_not_list | 验证_parse_json_list输入非列表JSON返回空列表 |  | 纯单元 |
| TestHelpers | model_to_schema_full | 验证_model_to_schema将完整Business对象转换为schema |  | 纯单元 |
| TestHelpers | model_to_schema_missing_coords | 验证_model_to_schema处理缺失坐标的Business对象 |  | 纯单元 |
| TestBusinessService | get_by_id_found | 通过ID查找商家，返回数据库中存在的商家对象 | asyncio | Mock服务 |
| TestBusinessService | get_by_id_not_found | 通过不存在的ID查找商家，返回None | asyncio | Mock服务 |
| TestBusinessService | list_businesses_default_source_db | 从数据库列出商家，使用默认源 | asyncio | Mock服务 |
| TestBusinessService | list_businesses_source_yelp_success | 从Yelp源成功列出商家 | asyncio | Mock服务 |
| TestBusinessService | list_businesses_source_yelp_error | Yelp源搜索商家时抛出错误 | asyncio | Mock服务 |
| TestBusinessService | list_businesses_sort_review_count | 按评论数排序列出商家 | asyncio | Mock服务 |
| TestBusinessService | list_businesses_sort_default | 使用未知排序方式，回退到默认排序列出商家 | asyncio | Mock服务 |
| TestBusinessService | list_businesses_empty | 使用不存在的关键词列出商家，返回空结果 | asyncio | Mock服务 |
| TestBusinessService | list_businesses_without_price | 不指定价格过滤列出商家 | asyncio | Mock服务 |

### test_favorite

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestListFavorites | list_favorites_empty | 空收藏列表应返回空列表。 | asyncio | Mock服务 |
| TestListFavorites | list_favorites_with_items | 收藏列表返回收藏项和分页信息。 | asyncio | Mock服务 |
| TestListFavorites | list_favorites_pagination | 分页参数应正确传递。 | asyncio | Mock服务 |
| TestAddFavorite | add_favorite_success | 添加收藏成功应返回收藏项信息。 | asyncio | Mock服务 |
| TestAddFavorite | add_favorite_shop_not_found | 商家不存在应抛出异常。 | asyncio | Mock服务 |
| TestAddFavorite | add_favorite_duplicate | 重复收藏应抛出异常。 | asyncio | Mock服务 |
| TestAddFavoriteYelpSource | add_yelp_favorite_success | Yelp 来源收藏成功应返回收藏项信息。 | asyncio, patch | Mock外部API |
| TestAddFavoriteYelpSource | add_yelp_favorite_not_found | Yelp 来源收藏时商家不存在应抛出异常。 | asyncio, patch | Mock外部API |
| TestAddFavoriteYelpSource | add_yelp_favorite_duplicate | Yelp 来源重复收藏应抛出异常。 | asyncio, patch | Mock外部API |
| TestRemoveFavorite | remove_favorite_success | 移除收藏成功。 | asyncio | Mock服务 |
| TestRemoveFavorite | remove_favorite_not_found | 收藏不存在应抛出异常。 | asyncio | Mock服务 |

### test_file

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestFileServiceDelete | delete_session_files_empty_username | 空 username 应直接返回。 |  | 纯单元 |
| TestFileServiceDelete | delete_session_files_empty_section_id | 空 section_id 应直接返回。 |  | 纯单元 |
| TestFileServiceDelete | delete_session_files_deletes_dir | 目录存在时应删除。 | patch | Mock外部API |
| TestFileServiceDelete | delete_session_files_not_exists | 目录不存在时应跳过。 | patch | Mock外部API |
| TestFileServiceDelete | delete_all_user_files_empty_username | 空 username 应直接返回。 |  | 纯单元 |
| TestFileServiceDelete | delete_all_user_files_deletes_dir | 目录存在时应删除。 | patch | Mock外部API |
| TestFileServiceDelete | load_doc_silent_on_failure | _load_doc 在 load_section_document 失败时不应抛异常。 | patch | Mock外部API |
| TestFileServiceDelete | load_doc_calls_llm | _load_doc 应调 load_section_document。 | patch | Mock外部API |

### test_review

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestHelpers | parse_json_field_valid | 解析有效的JSON字段返回字典 |  | 纯单元 |
| TestHelpers | parse_json_field_none | 解析None JSON字段返回None |  | 纯单元 |
| TestHelpers | parse_json_field_invalid | 解析无效JSON字段返回None |  | 纯单元 |
| TestHelpers | model_to_schema_with_user | 带用户信息的Review模型转换为Schema |  | 纯单元 |
| TestHelpers | model_to_schema_without_user | 不带用户信息的Review模型转换为Schema，user为None |  | 纯单元 |
| TestReviewService | list_by_business_default_source_db | 从数据库列出指定商家的评论（默认源） | asyncio | Mock服务 |
| TestReviewService | list_by_business_source_yelp_success | 从Yelp源成功列出评论 | asyncio | Mock服务 |
| TestReviewService | list_by_business_source_yelp_yelp_error | Yelp源获取评论时返回错误，抛出HTTPException | asyncio | Mock服务 |
| TestReviewService | list_by_business_rating_high | 按评分从高到低排序列出评论 | asyncio | Mock服务 |
| TestReviewService | list_by_business_rating_low | 按评分从低到高排序列出评论，返回空 | asyncio | Mock服务 |
| TestReviewService | list_by_business_empty | 列出不存在商家的评论，返回空结果 | asyncio | Mock服务 |
| TestReviewService | get_by_id_found | 通过ID找到评论，返回包含用户信息的ReviewBase | asyncio | Mock服务 |
| TestReviewService | get_by_id_not_found | 通过不存在的ID查找评论，返回None | asyncio | Mock服务 |

### test_yelp_search

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestYelpSearchService | to_business_detail_full | 将完整信息的Yelp商家Mock转换为BusinessDetail |  | 纯单元 |
| TestYelpSearchService | to_business_detail_minimal | 将最小信息的Yelp商家Mock转换为BusinessDetail |  | 纯单元 |
| TestYelpSearchService | search_no_location_raises | 不提供位置信息时搜索商家抛出ValueError | asyncio | Mock服务 |
| TestYelpSearchService | search_with_location | 使用location参数搜索Yelp商家 | asyncio | Mock服务 |
| TestYelpSearchService | search_with_lat_lng | 使用经纬度搜索Yelp商家 | asyncio | Mock服务 |
| TestYelpSearchService | search_with_all_filters | 使用所有过滤条件搜索Yelp商家 | asyncio | Mock服务 |
---

## 工具


### test_security

| 类 | 函数 | 描述 | 标记 | 类型 |
|:---:|:---:|:---:|:---:|:---:|
| TestPasswordHashing | hash_password_returns_string | 哈希密码返回非空字符串 |  | 纯单元 |
| TestPasswordHashing | hash_password_differs_from_plain | 哈希密码与明文不同 |  | 纯单元 |
| TestPasswordHashing | verify_password_correct | 正确密码验证通过 |  | 纯单元 |
| TestPasswordHashing | verify_password_incorrect | 错误密码验证失败 |  | 纯单元 |
| TestPasswordHashing | same_password_different_hashes | 同一密码每次哈希结果应不同（bcrypt 加盐）。 |  | 纯单元 |
| TestPasswordHashing | empty_password | 空密码的哈希和验证通过 |  | 纯单元 |
| TestJWTToken | create_token_returns_string | 创建JWT token返回字符串且格式正确 |  | 纯单元 |
| TestJWTToken | decode_token_valid | 解码有效JWT token返回正确payload |  | 纯单元 |
| TestJWTToken | decode_token_invalid | 解码无效JWT token返回None |  | 纯单元 |
| TestJWTToken | decode_token_expired | 过期 token 应返回 None。 |  | 纯单元 |
| TestJWTToken | token_contains_exp_claim | 创建的token包含exp过期时间声明 |  | 纯单元 |
| TestJWTToken | token_with_custom_expiry | 使用自定义过期时间创建JWT token |  | 纯单元 |
| TestJWTToken | create_token_with_additional_claims | 创建包含额外声明的JWT token |  | 纯单元 |
