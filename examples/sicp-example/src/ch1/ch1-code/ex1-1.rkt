#lang sicp

; 10
10

; 12
(+ 5 3 4)

; 8
(- 9 1)

; 3
(/ 6 2)

; (2*4) + (4-6) == 6
(+ (* 2 4) (- 4 6))

; nothing
(define a 3)

; nothing
(define b (+ a 1))

; (4+3+12) = 19
(+ a b (* a b))

; false (#f)
(= a b)

; (if (and true true) b a) == 4
(if (and (> b a) (< b (* a b)))
    b
    a)

; + 6 7 a = 16
(cond ((= a 4) 6)
      ((= b 4) (+ 6 7 a))
      (else 25))

; 2 + 4 = 6
(+ 2 (if (> b a) b a))

; 4*(a+1)=16
(* (cond ((> a b) a)
         ((< a b) b)
         (else -1))
   (+ a 1))
