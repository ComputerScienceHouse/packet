const gulp = require('gulp');
const exec = require('child_process').exec;

let ruffTask = (cb) => {
    exec('ruff check packet', function (err, stdout, stderr) {
        console.log(stdout);
        console.log(stderr);
        cb(err);
    });
};

gulp.task('ruff', ruffTask);