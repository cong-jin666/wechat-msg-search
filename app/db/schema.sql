-- FTS5 全文索引 + 与主表同步的触发器
-- 说明：使用普通（非 external content）FTS5 表，自己存一份分词结果。
-- 好处是删除/更新索引时不会有 external content 的 "database disk image is malformed" 风险，
-- 代价是多存一列分词文本（10 万条量级约几十 MB，个人项目可接受）。

CREATE VIRTUAL TABLE IF NOT EXISTS msg_fts USING fts5(
    segmented,
    tokenize = 'unicode61'
);

CREATE TRIGGER IF NOT EXISTS trg_msg_fts_ai
AFTER INSERT ON MSG
WHEN new.segmented_content IS NOT NULL AND new.segmented_content <> ''
BEGIN
    DELETE FROM msg_fts WHERE rowid = new.rowid;
    INSERT INTO msg_fts(rowid, segmented) VALUES (new.rowid, new.segmented_content);
END;

CREATE TRIGGER IF NOT EXISTS trg_msg_fts_au
AFTER UPDATE OF segmented_content ON MSG
WHEN new.segmented_content IS NOT NULL AND new.segmented_content <> ''
BEGIN
    DELETE FROM msg_fts WHERE rowid = new.rowid;
    INSERT INTO msg_fts(rowid, segmented) VALUES (new.rowid, new.segmented_content);
END;

CREATE TRIGGER IF NOT EXISTS trg_msg_fts_ad
AFTER DELETE ON MSG
BEGIN
    DELETE FROM msg_fts WHERE rowid = old.rowid;
END;
