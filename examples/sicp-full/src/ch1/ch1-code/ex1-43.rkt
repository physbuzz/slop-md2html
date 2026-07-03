#lang sicp
(define (square x) (* x x))
(define (inc x) (+ x 1))
(define (compose f g) (lambda (x) (f (g x))))
(define (repeated f n) 
  (if (= n 1)
    f
   (compose f (repeated f (- n 1)))))
((repeated square 2) 5)
((repeated inc 50) 1)
