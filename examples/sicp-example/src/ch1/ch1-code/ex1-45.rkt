#lang sicp
(define tolerance 0.00001)

(define (square x) (* x x))
(define (inc x) (+ x 1))
(define (average a b) (/ (+ a b) 2.0))

;; Conjecture, to find the nth root we need (floor (/ n 2)) damping steps
(define (average-damp f)
  (lambda (x)
    (average x (f x))))
(define (compose f g) (lambda (x) (f (g x))))
(define (repeated f n) 
  (if (= n 1)
    f
   (compose f (repeated f (- n 1)))))

(define (fixed-point f first-guess)
  (define (close-enough? v1 v2)
    (< (abs (- v1 v2))
       tolerance))
  (define (try guess)
    (let ((next (f guess)))
      (if (close-enough? guess next)
          next
          (try next))))
  (try first-guess))
(define (pow x n)
  (exp (* n (log x))))
(define (nth-root n x)
  (fixed-point 
	     ((repeated average-damp (floor (/ n 2))) (lambda (y) (/ x (pow y (- n 1)))))
	     1.0))

(nth-root 2 2.0)
(nth-root 3 2.0)
(nth-root 4 2.0)
(nth-root 5 2.0)
(nth-root 6 2.0)
(nth-root 7 2.0)
(nth-root 8 2.0)

