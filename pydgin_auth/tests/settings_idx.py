

OVERRIDE_SETTINGS_CHICP = \
    {'default': {
        'ELASTIC_URL': 'http://dev-elastic1:9200/',
        'IDX': {
            'CP_STATS_UD': {
                'name': 'cp:hg19_userdata_bed',
                'label': 'User Data',
                'idx_type': {},
                },
            'CP_STATS_IC': {
                'name': 'cp:hg19_immunochip_bed',
                'label': 'ImmunoChip',
                'idx_type': {
                    'IC-ATD_COOPER': {'label': "ATD - Cooper et al.", 'type': 'atd_cooper', 'auth_public': True},
                    'IC-CEL_TRYNKA': {'label': "CEL - Trynka et al.", 'type': 'cel_trynka', 'auth_public': True},
                    'IC-JIA_HINKS_UK': {'label': "JIA - Hinks et al. UK", 'type': 'jia_hinks_uk'},
                    'IC-MS_IMSGC': {'label': "MS - IMSGC et al.", 'type': 'ms_imsgc'},
                    'IC-NAR_FARACO': {'label': "NAR - Faraco et al.", 'type': 'nar_faraco'},
                    'IC-PBC_LIU': {'label': "PBC - Liu et al.", 'type': 'pbc_liu', 'auth_public': True},
                    'IC-RA_EYRE': {'label': "RA - Eyre et al.", 'type': 'ra_eyre', 'auth_public': True},
                    'IC-T1D_ONENGUT': {'label': 'T1D - Onengut et al.', 'type': 't1d_onengut', 'auth_public': True},
                },
                'auth_public': True,
            },
            'CP_STATS_GWAS': {
                'name': 'cp:hg19_gwas_bed',
                'label': 'GWAS Statistic',
                'idx_type': {
                    'GWAS-DUBOIS': {'label': 'CEL - Dubois et al.', 'type': 'cel_dubois',
                                    'auth_public': True},
                    'GWAS-FRANKE': {'label': 'CRO - Franke et al.', 'type': 'cro_franke',
                                    'auth_public': True},
                    'GWAS-IMSGC': {'label': 'MS - IMSGC et al.', 'type': 'ms_imsgc',
                                   'auth_public': True},
                    'GWAS-OKADA': {'label': 'RA - Okada et al.', 'type': 'ra_okada'},
                    'GWAS-STAHL': {'label': 'RA - Stahl et al.', 'type': 'ra_stahl'},
                    'GWAS-BARRETT': {'label': 'T1D - Barrett et al.', 'type': 't1d_barrett'},
                    'GWAS-COOPER': {'label': 'T1D - Cooper et al.', 'type': 't1d_cooper',
                                    'auth_public': True},
                    'GWAS-ANDERSON': {'label': 'UC - Anderson et al.', 'type': 'uc_anderson'},
                },
                'auth_public': True,
            },
            'TARGET_CHICAGO': {'name': 'cp:hg19_chicago_targets', 'label': 'CHICAGO',
                               'auth_public': True, },
            'TARGET_MIFSUD': {'name': 'cp:hg19_mifsud_gt_pm', 'label': 'Mifsud et al.', },
            'TARGET_MARTIN': {'name': 'cp:hg19_martin_pm', 'label': 'Martin et al.',
                              'auth_public': True, },
        },
        'TEST': 'auto_tests',
        'REPOSITORY': 'my_backup',
    }
    }


OVERRIDE_SETTINGS_PYDGIN = \
    {'default': {
        'ELASTIC_URL': 'http://dev-elastic1:9200/',
        'IDX': {
            'GENE': {
                'name': 'genes_hg38_v0.0.2',
                'idx_type': {
                    'GENE': {'type': 'gene', 'search': True, 'auth_public': True},
                    'PATHWAY': {'type': 'pathway_genesets', 'search': True},
                    'INTERACTIONS': {'type': 'interactions'}
                },
                'label': 'gene related indices',
                'suggester': True,
                'auth_public': True
            },
            'PUBLICATION': {
                'name': 'publications_v0.0.4',
                'idx_type': {
                    'PUBLICATION': {'type': 'publication', 'search': True}
                },
                'suggester': True,
                'auth_public': True
            },
            'MARKER': {
                'name': 'dbsnp144',
                'idx_type': {
                    'MARKER': {'type': 'marker', 'description': 'dbsnp', 'search': True, 'auth_public': True},
                    'HISTORY': {'type': 'rs_merge', 'description': 'snp merge history',
                                'search': True, 'auth_public': True},
                    'IC': {'type': 'immunochip', 'search': True}
                },
                'suggester': True,
                'auth_public': True
            },
            'DISEASE': {
                'name': 'disease',
                'idx_type': {
                    'DISEASE': {'type': 'disease', 'search': True}
                },
                'suggester': True,
            },
        },
        'TEST': 'auto_tests',
        'REPOSITORY': 'my_backup',
        'TEST_REPO_DIR': '/ipswich/data/pydgin/elastic/repos/test_snapshot/',
    }
    }
