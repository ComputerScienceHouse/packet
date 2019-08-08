/*
 gulpfile.js
 ===========
 Rather than manage one giant configuration file responsible
 for creating multiple tasks, each task has been broken out into
 its own file in gulpfile.js/tasks. Any files in that directory get
 automatically required below.

 To add a new task, simply add a new task file that directory.
 gulpfile.js/tasks/default.js specifies the default set of tasks to run
 when you run `gulp`.
 */

var requireDir = require('require-dir');
var gulp = require('gulp');

// Require all tasks in gulpfile.js/tasks, including subfolders
requireDir('./tasks', {recurse: true});

// CSS
gulp.task('css', ['sass:compile', 'css:minify']);

// Default task
gulp.task('default', ['css']);
gulp.task('production', ['css', 'generate-favicon', 'copy_secrets', 'pylint']);
