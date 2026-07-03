#lang sicp
(define (for-each lamb lst)
  (map lamb lst)
  (if #f nil))
(for-each
  (lambda (x) (newline) (display x))
  (list 57 321 88))
