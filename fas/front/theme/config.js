var theme= 'fedoraproject',
    srcPath = __dirname,
    themePath = __dirname + '/../../static/theme/' + theme;

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
                srcPath + '/tmp/theme.js'
            ]
        }
    }
};