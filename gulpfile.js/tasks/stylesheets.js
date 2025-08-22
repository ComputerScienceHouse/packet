const gulp = require("gulp");
const sass = require("gulp-sass")(require("sass"));
const cleanCSS = require("gulp-clean-css");
const rename = require("gulp-rename");

// Compile SCSS
gulp.task("sass:compile", () => {
  return gulp
    .src("frontend/scss/**/*.scss")
    .pipe(
      sass({
        outputStyle: "expanded",
      }).on("error", sass.logError),
    )
    .pipe(gulp.dest("packet/static/css"));
});

// Minify CSS
gulp.task("css:minify", () => {
  return gulp
    .src(["packet/static/css/*.css", "!packet/static/css/*.min.css"])
    .pipe(cleanCSS())
    .pipe(
      rename({
        suffix: ".min",
      }),
    )
    .pipe(gulp.dest("packet/static/css"));
});

// CSS
gulp.task("css", gulp.series("sass:compile", "css:minify"));
