--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: prem
--

COPY auth_group (id, name) FROM stdin;
3	CURATOR
2	DIL
1	READ
\.

--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--

SELECT pg_catalog.setval('auth_group_id_seq', coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_group";

--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: prem; Not copied
--

--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: prem; Not copied
--

--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: prem; Not copied
--

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--

SELECT pg_catalog.setval('auth_group_permissions_id_seq', coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_group_permissions";


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--

SELECT pg_catalog.setval('auth_permission_id_seq', coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_permission";


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: prem
--

COPY auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
5	pbkdf2_sha256$20000$oGNfCvP92wP6$kp32dEh7L34czRF+t4e7cZ4JgXEn4GhvBn3rIY1crnE=	2015-08-04 17:20:32.689239+01	f	prem_dil			prem.dil@dummy.xxx	f	t	2015-07-22 13:09:28+01
3	pbkdf2_sha256$20000$T02Ktf3IpbhF$2ZiXuYHYAtNiLQkrmiiZUwJmPsb4mtGV4kzc/+5WVAE=	2015-08-05 09:26:56.360424+01	f	prem_ro			prem.ro@dummy.xxx	f	t	2015-07-22 11:33:35.424898+01
6	pbkdf2_sha256$20000$Ba1MF9jdjCLF$WuC075BcgzkrAf4ShVGgZO6FviNYlnfEngOF4za9L6k=	2015-07-30 15:16:57.951831+01	f	prem_curator			prem.cur@dummy.xxx	f	t	2015-07-22 13:10:15+01
10	pbkdf2_sha256$20000$Wi2WC2wYikwm$oDDuxs9iLOSw+F5PGouyMmN6vib37jafNgotOD9IOcw=	2015-07-31 14:18:28.307727+01	f	dummyuser			dummy@dummy.com	f	t	2015-07-31 14:18:28.194449+01
11	pbkdf2_sha256$20000$StXVdtds49Of$wHQLXChZs/5SauBZHhboaVjoFHlYx7+0h16ih04LK1M=	2015-07-31 14:20:53.518653+01	f	testuser			test@testmail.com	f	t	2015-07-31 14:20:53.413251+01
1	pbkdf2_sha256$20000$WB0wuebUGDZT$RDeQG/w6ahCfEZ8pUaIsFbz0KLa1l3uM48s6uUPPhCY=	2015-08-04 16:38:40.12695+01	t	admin			premanand.achuthan@cimr.cam.ac.uk	t	t	2015-07-22 11:15:09.182062+01
12	pbkdf2_sha256$20000$HJpA8iucSRqf$Ti3MaStTmS+AnKJROgVYQtPmhQJ5itOvZhScbS7xClg=	2015-10-21 10:36:09+01	f	ellen.schofield	Ellen	Schofield	ellen.schofield@cimr.cam.ac.uk	t	t	2015-10-21 10:33:22+01
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: prem
--

COPY auth_user_groups (id, user_id, group_id) FROM stdin;
2	3	1
8	6	1
9	6	3
10	5	1
11	5	2
15	10	1
16	11	1
20	12	1
21	12	2
\.


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--

SELECT pg_catalog.setval('auth_user_groups_id_seq', coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_user_groups";


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--

SELECT pg_catalog.setval('auth_user_id_seq', coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_user";

--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: prem
--

COPY auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--

--SELECT pg_catalog.setval('auth_user_user_permissions_id_seq', 1, false);
SELECT pg_catalog.setval('auth_user_user_permissions_id_seq', coalesce(max("id"), 1), max("id") IS NOT null) FROM "auth_user_user_permissions";


--
-- Data for Name: authtoken_token; Type: TABLE DATA; Schema: public; Owner: prem
--

COPY authtoken_token (key, created, user_id) FROM stdin;
f78a60ebe895d81199430d33fd05ca01c6d8557c	2015-07-24 15:56:55.671414+01	3
66d6ede5ab498afa052f2deb4552ffb56c612798	2015-07-24 15:59:01.600009+01	5
ee2a620269a19eeecff1a01d95c66b7f50b9fd2d	2015-07-31 14:18:28.252227+01	10
ceb7f8da042cdfb3df4a829ad28c59ee577f5132	2015-07-31 14:20:53.465311+01	11
fa9d3023e0a31cc6bd40ddb0cf337ebbcf176974	2015-07-31 14:20:53.469208+01	6
76f82eafbd169a0676220fdacbb13b706f4be81b	2015-07-31 14:20:53.474583+01	1
c599001e0a5418bf7dbbddf59aa6a3408785fad1	2015-10-21 10:33:22.95711+01	12
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: prem Not copied
--

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--

SELECT pg_catalog.setval('django_content_type_id_seq', coalesce(max("id"), 1), max("id") IS NOT null) FROM "django_content_type";


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: prem Not copied
--

--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: prem Not copied
--

--
-- Data for Name: pydgin_auth_userprofile; Type: TABLE DATA; Schema: public; Owner: prem
--

COPY pydgin_auth_userprofile (id, user_id, is_terms_agreed) FROM stdin;
1	3	f
3	5	f
4	6	f
7	1	f
9	10	t
10	11	t
11	12	t
\.


--
-- Name: pydgin_auth_userprofile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: prem
--

SELECT pg_catalog.setval('pydgin_auth_userprofile_id_seq', coalesce(max("id"), 1), max("id") IS NOT null) FROM "pydgin_auth_userprofile";


--
-- PostgreSQL database dump complete
--

