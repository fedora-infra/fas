var theme= 'default',
    srcPath = __dirname,
    themePath = __dirname + '/../../theme/'+theme+'/static/';

module.exports = {
    theme : theme,
    less: {
        paths: {
            src: srcPath + '/less',
            dist: themePath + '/style',
            filename : 'fas.css'
        },
        compilation: {
            options: {
                compress: true,
                cleancss: true,
                strictImports: true,
                strictUnits: true,
                strictMath: false,
                sourceMap: true,
                globalVar: '',
                modifyVars: {},
                paths: ['vendor']
            }
        }
    },
    js: {
        paths: {
            src: srcPath + '/js',
            tmp: srcPath + '/tmp',
            dist: themePath + '/js',
            filename: 'fas.js',
        },
        compilation: {
            options: {
                mangle: false,
                compress: true,
                output: {
                    beautify: false
                }
            }
        },
        files: {
            'theme.js': [
                'vendor/jquery/dist/jquery.min.js',
                'vendor/bootstrap/dist/js/bootstrap.js',
                'vendor/bootstrap-table/dist/bootstrap-table.min.js',
                'vendor/NotificationStyles/js/classie.js',
                'vendor/NotificationStyles/js/modernizr.custom.js',
                'vendor/NotificationStyles/js/notificationFx.js',
                srcPath + '/tmp/theme.js'
            ]
        }
    }
};
