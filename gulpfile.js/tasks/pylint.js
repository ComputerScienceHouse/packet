const gulp = require('gulp');
const exec = require('child_process').exec;

let pylintTask = (cb) => {
    exec('pylint packet', function (err, stdout, stderr) {
        console.log(stdout);
        console.log(stderr);
        cb(err);
    });
};

gulp.task('pylint', pylintTask);
