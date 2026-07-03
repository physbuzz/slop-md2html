#lang sicp

; Helper functions
(define (id x) x)
(define (next x) (+ x 1))
(define (square x) (* x x))
(define (next2 x) (+ x 2))

; product defns
(define (product term a next b)
  (if (> a b)
      1
      (* (term a)
         (product term (next a) next b))))
(define (product-iter term a next b)
  (define (iter a result)
    (if (> a b)
        result
        (iter (next a) (* result (term a)))))
  (iter a 1))

; Implement factorial and wallis product.
(define (fact a)
  (product id 1 next a))
(define (fact-iter a)
  (product-iter id 1 next a))
(define (wallis-term x) (/ (* x (+ x 2)) (square (+ x 1))))
(define (wallis-pi nterms)
  (* 4 (product wallis-term 2.0 next2 nterms)))
(define (wallis-pi-iter nterms)
  (* 4 (product-iter wallis-term 2.0 next2 nterms)))

; Pretty print
(display "Factorial (linear recursive, then iterative)") 
(newline)
(fact 5)
(fact-iter 5)
(newline)
(newline)
(display "Wallis pi")
(newline)
(wallis-pi 100)
(wallis-pi-iter 100)
