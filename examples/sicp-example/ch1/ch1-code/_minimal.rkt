#lang rosette

; Reference implementation
(define (sum-largest-squares-spec a b c)
  (define sorted (sort (list a b c) >))
  (+ (* (first sorted) (first sorted))
     (* (second sorted) (second sorted))))

; Test cases
(define test-cases
  (list (list 1 2 3)    ; Expected: 13
        (list 3 2 1)    ; Expected: 13
        (list 5 5 1)    ; Expected: 50
        (list 3 7 4)    ; Expected: 65
        (list 9 3 6)))  ; Expected: 117

; Symbolic variables for hole-based synthesis
(define-symbolic a b c integer?)

; Sketch for the solution - we'll fill in the holes
(define (sketch a b c)
  (define h1 (choose a b c))
  (define h2 (choose a b c))
  (define condition (choose (< a b) (< a c) (< b c)))

  (if condition
      (+ (* h1 h1) (* h2 h2))
      (+ (* (choose a b c) (choose a b c))
         (* (choose a b c) (choose a b c)))))

; Define a synthesis condition
(define condition
  (assert (= (sum-largest-squares-spec a b c)
             (sketch a b c))))

; Find a solution
(define solution
  (synthesize #:forall (list a b c)
              #:guarantee condition))

; Print the solution
(displayln "Synthesized Solution:")
(displayln (evaluate sketch solution))

; Testing
(displayln "\nTesting with examples:")
(for ([test test-cases])
  (define a (first test))
  (define b (second test))
  (define c (third test))
  (define expected (sum-largest-squares-spec a b c))
  (define actual (evaluate (sketch a b c) solution))
  (printf "For (~a ~a ~a): Expected: ~a, Got: ~a\n"
          a b c expected actual))
