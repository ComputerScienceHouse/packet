var gulp = require('gulp');
var exec = require('child_process').exec;

var pylintTask = function (cb) {
    exec('pylint packet', function (err, stdout, stderr) {
        console.log(stdout);
        console.log(stderr);
        cb(err);
    });
}

gulp.task('pylint', pylintTask);
