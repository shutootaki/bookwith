-- H-21: Supabase Auth と組み合わせた行レベルセキュリティ。
--
-- 各テーブルで `auth.uid() = user_id` のポリシーを敷く。
-- 現状のテーブルは FastAPI の SQLAlchemy で `public` schema に作成されるため
-- PostgREST 経由でも到達可能。RLS が無いと `anon` キーで全件読まれる。
--
-- 既存テーブル（books, chats, messages, annotations, podcasts, users）に対し、
-- 1) RLS を有効化
-- 2) auth.uid() ベースの SELECT/INSERT/UPDATE/DELETE ポリシーを定義する
--
-- メッセージは chat 経由の所有者なので chats を join して評価する。

-- ============================================================
-- Helper: テーブルの存在チェックは pg_class を見る。
-- ============================================================

DO $$
BEGIN
    -- users
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users') THEN
        EXECUTE 'ALTER TABLE public.users ENABLE ROW LEVEL SECURITY';
        EXECUTE 'ALTER TABLE public.users FORCE ROW LEVEL SECURITY';
        EXECUTE 'DROP POLICY IF EXISTS users_self_select ON public.users';
        EXECUTE 'CREATE POLICY users_self_select ON public.users FOR SELECT USING (id::text = auth.uid()::text)';
        EXECUTE 'DROP POLICY IF EXISTS users_self_update ON public.users';
        EXECUTE 'CREATE POLICY users_self_update ON public.users FOR UPDATE USING (id::text = auth.uid()::text) WITH CHECK (id::text = auth.uid()::text)';
    END IF;

    -- books
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'books') THEN
        EXECUTE 'ALTER TABLE public.books ENABLE ROW LEVEL SECURITY';
        EXECUTE 'ALTER TABLE public.books FORCE ROW LEVEL SECURITY';
        EXECUTE 'DROP POLICY IF EXISTS books_owner_all ON public.books';
        EXECUTE 'CREATE POLICY books_owner_all ON public.books FOR ALL USING (user_id::text = auth.uid()::text) WITH CHECK (user_id::text = auth.uid()::text)';
    END IF;

    -- chats
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'chats') THEN
        EXECUTE 'ALTER TABLE public.chats ENABLE ROW LEVEL SECURITY';
        EXECUTE 'ALTER TABLE public.chats FORCE ROW LEVEL SECURITY';
        EXECUTE 'DROP POLICY IF EXISTS chats_owner_all ON public.chats';
        EXECUTE 'CREATE POLICY chats_owner_all ON public.chats FOR ALL USING (user_id::text = auth.uid()::text) WITH CHECK (user_id::text = auth.uid()::text)';
    END IF;

    -- annotations
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'annotations') THEN
        EXECUTE 'ALTER TABLE public.annotations ENABLE ROW LEVEL SECURITY';
        EXECUTE 'ALTER TABLE public.annotations FORCE ROW LEVEL SECURITY';
        EXECUTE 'DROP POLICY IF EXISTS annotations_via_book ON public.annotations';
        EXECUTE $POL$
            CREATE POLICY annotations_via_book ON public.annotations FOR ALL
            USING (
                EXISTS (
                    SELECT 1 FROM public.books b
                    WHERE b.id = annotations.book_id
                      AND b.user_id::text = auth.uid()::text
                )
            )
            WITH CHECK (
                EXISTS (
                    SELECT 1 FROM public.books b
                    WHERE b.id = annotations.book_id
                      AND b.user_id::text = auth.uid()::text
                )
            )
        $POL$;
    END IF;

    -- messages
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'messages') THEN
        EXECUTE 'ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY';
        EXECUTE 'ALTER TABLE public.messages FORCE ROW LEVEL SECURITY';
        EXECUTE 'DROP POLICY IF EXISTS messages_via_chat ON public.messages';
        EXECUTE $POL$
            CREATE POLICY messages_via_chat ON public.messages FOR ALL
            USING (
                EXISTS (
                    SELECT 1 FROM public.chats c
                    WHERE c.id = messages.chat_id
                      AND c.user_id::text = auth.uid()::text
                )
            )
            WITH CHECK (
                EXISTS (
                    SELECT 1 FROM public.chats c
                    WHERE c.id = messages.chat_id
                      AND c.user_id::text = auth.uid()::text
                )
            )
        $POL$;
    END IF;

    -- podcasts
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'podcasts') THEN
        EXECUTE 'ALTER TABLE public.podcasts ENABLE ROW LEVEL SECURITY';
        EXECUTE 'ALTER TABLE public.podcasts FORCE ROW LEVEL SECURITY';
        EXECUTE 'DROP POLICY IF EXISTS podcasts_owner_all ON public.podcasts';
        EXECUTE 'CREATE POLICY podcasts_owner_all ON public.podcasts FOR ALL USING (user_id::text = auth.uid()::text) WITH CHECK (user_id::text = auth.uid()::text)';
    END IF;
END$$;

-- 注: FastAPI が SERVICE_ROLE_KEY を使用して接続する場合、`bypassrls` 権限が
-- 付与されているため上記ポリシーは適用されない（=API 側で所有者検証を継続必須）。
-- anon / 認証ユーザー JWT 経由でアクセスされた際の漏洩防止としての防衛線。
