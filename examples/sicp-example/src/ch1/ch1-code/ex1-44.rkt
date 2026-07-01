#lang sicp
(define (square x) (* x x))
(define (inc x) (+ x 1))
(define (compose f g) (lambda (x) (f (g x))))
(define (repeated f n) 
  (if (= n 1)
    f
   (compose f (repeated f (- n 1)))))
(define dx 0.05)
(define (smooth f) (lambda (x) (/ (+ (f (+ x dx)) (f x) (f (- x dx))) 3)))

((smooth abs) 0)
(((repeated smooth 4) abs) 0)
(((repeated smooth 4) abs) 1.0)
