#lang racket

(define quoted-list '(a b c))
(define list-of-quotes (list 'a 'b 'c))

(displayln "Are (list 'a 'b 'c) and '(a b c) structurally equal?")
(displayln (equal? (list 'a 'b 'c) '(a b c))) ; => #t
(displayln (equal? (list (quote a) (quote b) (quote c)) 
                   (quote (a b c)))) ; => #t
