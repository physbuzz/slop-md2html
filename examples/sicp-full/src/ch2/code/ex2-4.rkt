#lang sicp
(define (cons x y) (lambda (m) (m x y)))
(define (car z) (z (lambda (p q) p)))
(define (cdr z) (z (lambda (p q) q)))
(let ((arg (cons 1 2)))
  (display (car arg))
  (newline)
  (display (cdr arg)))
