var gulp = require('gulp');
var cleanCSS = require('gulp-clean-css');
var rename = require("gulp-rename");

// Minify CSS
gulp.task('css:minify', ['sass:compile'], function() {
  return gulp.src([
      'packet/static/css/*.css',
      '!packet/static/css/*.min.css'
    ])
    .pipe(cleanCSS())
    .pipe(rename({
      suffix: '.min'
    }))
    .pipe(gulp.dest('packet/static/css'));
});
