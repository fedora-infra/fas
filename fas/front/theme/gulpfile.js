'use strict';

// =============================================================================
// Global Vars =================================================================
// =============================================================================

// Global requirements
var gulp = require('gulp'),
    notification = require('node-notifier'),
    $ = require('gulp-load-plugins')(),
    eventStream = require('event-stream'),
    fs = require('fs');

var config = require('./config');


// =============================================================================
// Local lib ===================================================================
// =============================================================================

// Dev desktop notification
var notifier = new notification();
function notifyUser(title, message) {
    notifier.notify({
        title: title,
        message: message,
        hint: 'int:transient:1'
    });
}


// =============================================================================
// Style =======================================================================
// =============================================================================

// Compilation
gulp.task('less', function() {
    return gulp.src( config.less.paths.src + '/*.less' )
        .pipe(
            $.less( config.less.compilation.options )
            .on('error', function(err) {
                notifyUser('Style', 'Less compilation failed');
                console.error('Less compilation error: ' + err.message);
                this.emit('end');
            })
        )
        .pipe($.concat( config.less.paths.filename ))
        .pipe(gulp.dest( config.less.paths.dist ));
});


// =============================================================================
// Javascript ==================================================================
// =============================================================================

gulp.task('js:browserify', function() {
    gulp.src( config.js.paths.src + '/*.js' )
        .pipe($.browserify())
        .pipe(gulp.dest( config.js.paths.tmp ));
});

gulp.task('js', ['js:browserify'], function() {
    var src = config.js.files || {};
    var me = this;
    return eventStream.merge.apply(eventStream, Object.keys(src).map(function(dest) {
        var files = this[dest];

        for(var k in files) {
            if(!fs.existsSync(files[k])) {
                console.error('Javascript concatenation failed: file "' + files[k] + '" not found');
                me.emit('end');
            }
        }

        console.info('Javascript concatenation: file ' + dest);
        return gulp.src(files)
            .pipe($.concat(dest))
            .pipe($.uglify({
                mangle: false,
                compress: true,
                output: {
                    beautify: false
                }
            }))
            .pipe(gulp.dest( config.js.paths.dist ));
    }, src));
});


// =============================================================================
// Watcher =====================================================================
// =============================================================================

// Rebuild compiled files on source changes
gulp.task('watch', function() {
    gulp.watch( config.less.paths.src + '/**/*.less', ['less'] );
    gulp.watch( [config.js.paths.src + '/**/*.js', 'config.js'], ['js'] );
});