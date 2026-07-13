--
-- PostgreSQL database dump
--

\restrict fPHLKloFJ4Lg1y4dDvnMNJkq9N2WYhUfbn7FqkFvjEHvbhff5MutgEkRjF1EgJe

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg12+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg12+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: unaccent; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;


--
-- Name: EXTENSION unaccent; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION unaccent IS 'text search dictionary that removes accents';


--
-- Name: vector; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;


--
-- Name: EXTENSION vector; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION vector IS 'vector data type and ivfflat and hnsw access methods';


--
-- Name: f_unaccent(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.f_unaccent(text) RETURNS text
    LANGUAGE sql IMMUTABLE STRICT PARALLEL SAFE
    AS $_$ SELECT public.unaccent('public.unaccent', $1) $_$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: chat_conversations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.chat_conversations (
    id character varying(36) NOT NULL,
    user_id character varying(64) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_active_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: click_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.click_events (
    id character varying(32) NOT NULL,
    user_id character varying(64) NOT NULL,
    query_id integer,
    target_type character varying(32) NOT NULL,
    target_ref character varying(256),
    target_url text NOT NULL,
    rendered_at timestamp with time zone DEFAULT now() NOT NULL,
    clicked_at timestamp with time zone
);


--
-- Name: conversation_messages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conversation_messages (
    id integer NOT NULL,
    conversation_id character varying(36) NOT NULL,
    role character varying(16) NOT NULL,
    content text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: conversation_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.conversation_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: conversation_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.conversation_messages_id_seq OWNED BY public.conversation_messages.id;


--
-- Name: feedback_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.feedback_events (
    id integer NOT NULL,
    user_id character varying(64) NOT NULL,
    scope character varying(16) NOT NULL,
    query_id integer,
    click_id character varying(32),
    rating smallint,
    comment text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: feedback_events_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.feedback_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: feedback_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.feedback_events_id_seq OWNED BY public.feedback_events.id;


--
-- Name: passages; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.passages (
    id integer NOT NULL,
    source character varying(64) NOT NULL,
    source_ref character varying(256) NOT NULL,
    lang character varying(8) NOT NULL,
    title text,
    body text NOT NULL,
    subjects text[],
    embedding public.vector(1024),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS ((setweight(to_tsvector('english'::regconfig, public.f_unaccent(COALESCE(title, ''::text))), 'A'::"char") || setweight(to_tsvector('english'::regconfig, public.f_unaccent(COALESCE(body, ''::text))), 'B'::"char"))) STORED
);


--
-- Name: passages_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.passages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: passages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.passages_id_seq OWNED BY public.passages.id;


--
-- Name: query_log; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.query_log (
    id integer NOT NULL,
    user_id character varying(64) NOT NULL,
    raw_query text NOT NULL,
    lang character varying(8),
    extracted_filters jsonb,
    retrieved_passage_ids integer[],
    shown_database_slugs character varying[],
    answer_text text,
    model_name character varying(64),
    latency_ms integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: query_log_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.query_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: query_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.query_log_id_seq OWNED BY public.query_log.id;


--
-- Name: sessions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sessions (
    id character varying(64) NOT NULL,
    user_id character varying(64) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL
);


--
-- Name: subscription_databases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.subscription_databases (
    id integer NOT NULL,
    slug character varying(64) NOT NULL,
    name character varying(200) NOT NULL,
    vendor character varying(200),
    url text NOT NULL,
    content_types character varying[],
    subjects character varying[],
    languages character varying[],
    access_method character varying(64),
    description_en text,
    description_ar text,
    description_de text,
    enabled boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: subscription_databases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.subscription_databases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: subscription_databases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.subscription_databases_id_seq OWNED BY public.subscription_databases.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id character varying(64) NOT NULL,
    email_domain character varying(128) NOT NULL,
    department character varying(128),
    role character varying(16) DEFAULT 'user'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_seen_at timestamp with time zone
);


--
-- Name: conversation_messages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages ALTER COLUMN id SET DEFAULT nextval('public.conversation_messages_id_seq'::regclass);


--
-- Name: feedback_events id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_events ALTER COLUMN id SET DEFAULT nextval('public.feedback_events_id_seq'::regclass);


--
-- Name: passages id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.passages ALTER COLUMN id SET DEFAULT nextval('public.passages_id_seq'::regclass);


--
-- Name: query_log id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_log ALTER COLUMN id SET DEFAULT nextval('public.query_log_id_seq'::regclass);


--
-- Name: subscription_databases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_databases ALTER COLUMN id SET DEFAULT nextval('public.subscription_databases_id_seq'::regclass);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: chat_conversations chat_conversations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_conversations
    ADD CONSTRAINT chat_conversations_pkey PRIMARY KEY (id);


--
-- Name: click_events click_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.click_events
    ADD CONSTRAINT click_events_pkey PRIMARY KEY (id);


--
-- Name: conversation_messages conversation_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_pkey PRIMARY KEY (id);


--
-- Name: feedback_events feedback_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_events
    ADD CONSTRAINT feedback_events_pkey PRIMARY KEY (id);


--
-- Name: passages passages_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.passages
    ADD CONSTRAINT passages_pkey PRIMARY KEY (id);


--
-- Name: query_log query_log_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_log
    ADD CONSTRAINT query_log_pkey PRIMARY KEY (id);


--
-- Name: sessions sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_pkey PRIMARY KEY (id);


--
-- Name: subscription_databases subscription_databases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_databases
    ADD CONSTRAINT subscription_databases_pkey PRIMARY KEY (id);


--
-- Name: subscription_databases subscription_databases_slug_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.subscription_databases
    ADD CONSTRAINT subscription_databases_slug_key UNIQUE (slug);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_chat_conversations_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_chat_conversations_user_id ON public.chat_conversations USING btree (user_id);


--
-- Name: ix_click_query; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_click_query ON public.click_events USING btree (query_id);


--
-- Name: ix_click_target_clicked; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_click_target_clicked ON public.click_events USING btree (target_type, target_ref, clicked_at);


--
-- Name: ix_conversation_messages_conv_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_conversation_messages_conv_id ON public.conversation_messages USING btree (conversation_id);


--
-- Name: ix_passages_embedding_hnsw; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_passages_embedding_hnsw ON public.passages USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: ix_passages_search_vector; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_passages_search_vector ON public.passages USING gin (search_vector);


--
-- Name: ix_passages_subjects; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_passages_subjects ON public.passages USING gin (subjects);


--
-- Name: ix_passages_title_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_passages_title_trgm ON public.passages USING gin (title public.gin_trgm_ops);


--
-- Name: ix_query_log_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_query_log_created ON public.query_log USING btree (created_at);


--
-- Name: ix_query_log_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_query_log_user_created ON public.query_log USING btree (user_id, created_at);


--
-- Name: ix_sessions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sessions_user_id ON public.sessions USING btree (user_id);


--
-- Name: ix_sub_db_subjects; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_sub_db_subjects ON public.subscription_databases USING gin (subjects);


--
-- Name: chat_conversations chat_conversations_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.chat_conversations
    ADD CONSTRAINT chat_conversations_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: click_events click_events_query_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.click_events
    ADD CONSTRAINT click_events_query_id_fkey FOREIGN KEY (query_id) REFERENCES public.query_log(id);


--
-- Name: click_events click_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.click_events
    ADD CONSTRAINT click_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: conversation_messages conversation_messages_conversation_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conversation_messages
    ADD CONSTRAINT conversation_messages_conversation_id_fkey FOREIGN KEY (conversation_id) REFERENCES public.chat_conversations(id) ON DELETE CASCADE;


--
-- Name: feedback_events feedback_events_click_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_events
    ADD CONSTRAINT feedback_events_click_id_fkey FOREIGN KEY (click_id) REFERENCES public.click_events(id);


--
-- Name: feedback_events feedback_events_query_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_events
    ADD CONSTRAINT feedback_events_query_id_fkey FOREIGN KEY (query_id) REFERENCES public.query_log(id);


--
-- Name: feedback_events feedback_events_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.feedback_events
    ADD CONSTRAINT feedback_events_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: query_log query_log_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.query_log
    ADD CONSTRAINT query_log_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: sessions sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sessions
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

\unrestrict fPHLKloFJ4Lg1y4dDvnMNJkq9N2WYhUfbn7FqkFvjEHvbhff5MutgEkRjF1EgJe

