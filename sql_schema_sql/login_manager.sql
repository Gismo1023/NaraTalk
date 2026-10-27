SELECT id_manager, manager_name
FROM public.manager
WHERE password_hash = crypt(%s, password_hash)
LIMIT 1;