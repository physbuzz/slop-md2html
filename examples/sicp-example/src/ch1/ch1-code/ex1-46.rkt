#lang sicp

(define (average a b) (/ (+ a b) 2.0))

(define (iterative-improve good-enough? improve)
  (lambda (guess) 
    (let ((guess2 (improve guess)))
      (if (good-enough? guess guess2)
	guess2
	((iterative-improve good-enough? improve) guess2)
      ))))

(define tolerance 0.0001)
(define (my-close-enough? v1 v2)
  (< (abs (- v1 v2))
     tolerance))
(define (my-sqrt x)
  ((iterative-improve 
     my-close-enough? 
    (lambda (guess) (average guess (/ x guess)))) 1.0))

(define (fixed-point f first-guess)
  ((iterative-improve my-close-enough? f) first-guess))

(my-sqrt 2.0)

(fixed-point cos 1.0)
