l = [
 {
    'enum':0,
    'tag':'types',
    'descr':'Data structures',
    'symbols':[ 'dbcsr_obj',
                'dbcsr_distribution_obj',
                'dbcsr_iterator',
                'dbcsr_scalar_type' ]
 }, {
    'enum':1,
    'tag':'general_init',
    'descr':'Library and parallel environment initialization/release',
    'symbols':[ 'dbcsr_mp_new',
                'dbcsr_init_lib',
                'dbcsr_set_default_config',
                'dbcsr_finalize_lib',
                'dbcsr_mp_release' ]
 }, {
    'enum':2,
    'tag':'distribution',
    'descr':'Distribution setup/release/inquiry',
    'symbols':[ 'dbcsr_distribution_init',
                'dbcsr_distribution_new',
                'dbcsr_distribution',
                'dbcsr_distribution_release' ]
 }, {
    'enum':3,
    'tag':'matrix_init',
    'descr':'Creation/release of a DBCSR matrix',
    'symbols':[ 'dbcsr_init',
                'dbcsr_create',
                'dbcsr_work_create',
                'dbcsr_finalize',
                'dbcsr_release' ]
 }, {
    'enum':4,
    'tag':'matrix_set',
    'descr':'Setting the matrix elements',
    'symbols':[ 'dbcsr_put_block',
                'dbcsr_get_block_p',
                'dbcsr_reserve_block2d',
                'dbcsr_set' ]
 }, {
    'enum':5,
    'tag':'matrix_manipul',
    'descr':'DBCSR matrix data manipulation',
    'symbols':[ 'dbcsr_copy',
                'dbcsr_copy_into_existing',
                'dbcsr_new_transposed',
                'dbcsr_scale',
                'dbcsr_filter',
                'dbcsr_desymmetrize_deep',
                'dbcsr_add_on_diag' ]

 }, {
    'enum':6,
    'tag':'matrix_ops',
    'descr':'Operations between DBCSR matrices',
    'symbols':[ 'dbcsr_add',
                'dbcsr_multiply' ]
 }, {
    'enum':7,
    'tag':'iterator',
    'descr':'Iterators related facilities',
    'symbols':[ 'dbcsr_iterator_start',
                'dbcsr_iterator_stop',
                'dbcsr_iterator_blocks_left',
                'dbcsr_iterator_next_block' ]
 }, {
    'enum':8,
    'tag':'inquiry',
    'descr':'General DBCSR matrix inquiry',
    'symbols':[ 'dbcsr_get_info',
                'dbcsr_get_occupation',
                'dbcsr_name',
                'dbcsr_get_matrix_type',
                'dbcsr_get_data_type',
                'dbcsr_checksum' ]
 }, {
    'enum':9,
    'tag':'index_inquiry',
    'descr':'Indices/sizes matrix inquiry',
    'symbols':[ 'array_data',
                'dbcsr_get_data_size',
                'dbcsr_get_stored_coordinates',
                'dbcsr_nblkrows_total',
                'dbcsr_nblkcols_total' ]
 }, {
    'enum':10,
    'tag':'data_inquiry',
    'descr':'Data-related DBCSR matrix inquiry',
    'symbols':[ 'dbcsr_trace',
                'dbcsr_get_diag',
                'dbcsr_frobenius_norm',
                'dbcsr_norm' ]
 }, {
    'enum':11,
    'tag':'eigenval',
    'descr':'Eigenvalues estimate with Arnoldi',
    'symbols':[ 'dbcsr_arnoldi_extremal',
                'dbcsr_arnoldi_ev' ]
 },
]
