const gulp = require('gulp');
const minify = require('gulp-minify');

gulp.task('js:minify', (done) => {
    gulp.src([
        'packet/static/js/*.js',
        '!packet/static/js/*.min.js'
    ])
        .pipe(minify({
            ext: {
                src: '.js',
                min: '.min.js'
            },
            ignoreFiles: ['.min.js']
        }))
        .pipe(gulp.dest('packet/static/js'));
    done();
});

// JS
gulp.task('js', gulp.series('js:minify'));
