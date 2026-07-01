#lang sicp

(define (average x y) 
  (/ (+ x y) 2))

(define (improve guess x)
  (average guess (/ x guess)))

(define (square x) 
  (* x x))

(define (good-enough? guess x)
  (< (abs (- (square guess) x)) 0.001))

(define (sqrt-iter guess x)
  (if (good-enough? guess x)
      guess
      (sqrt-iter (improve guess x) x)))

(define (my-sqrt x)
  (sqrt-iter 1.0 x))

(my-sqrt 2.0)

; The version which uses the new-if statement hangs!
; (define (new-if predicate 
;                then-clause 
;                else-clause)
;  (cond (predicate then-clause)
;        (else else-clause)))

; This version also hangs:
; (define (new-if predicate then-clause else-clause)
;   (if predicate then-clause else-clause))
; (define (sqrt-iter2 guess x)
;   (new-if (good-enough? guess x)
;           guess
;           (sqrt-iter2 (improve guess x) x)))
; (define (my-sqrt2 x)
;   (sqrt-iter2 1.0 x))
;  (my-sqrt2 2.0)
