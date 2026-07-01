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

; Given the last and 2nd last guesses, check if the fractional change is good enough.
; I'm choosing the formula |guessL-guessLL|/guessL < 0.001
(define (good-enough2? guessL guessLL) 
  (< (/ (abs (- guessL guessLL)) guessL) 0.01))

(define (sqrt-iter2 guessL guessLL x)
  (if (good-enough2? guessL guessLL)
      guessL
      (sqrt-iter2 (improve guessL x) guessL x)))

(define (my-sqrt2 x)
  (sqrt-iter2 1.0 1.1 x))

(my-sqrt 0.0001)
(my-sqrt2 0.0001)
