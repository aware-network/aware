CREATE TABLE public.tag (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE public.user_tag (
    user_id UUID NOT NULL REFERENCES public.user(id),
    tag_id UUID NOT NULL REFERENCES public.tag(id),
    PRIMARY KEY (user_id, tag_id)
);

COMMENT ON TABLE public.tag IS 'Tags that can be applied to users';
COMMENT ON TABLE public.user_tag IS 'Mapping between users and tags';
COMMENT ON COLUMN public.user_tag.user_id IS 'reverse';
COMMENT ON COLUMN public.user_tag.tag_id IS 'forward';
