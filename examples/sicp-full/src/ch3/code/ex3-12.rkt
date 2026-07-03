#lang sicp

(define (append! x y)
  (set-cdr! (last-pair x) y)
  x)

(define (last-pair x)
  (if (null? (cdr x))
      x
      (last-pair (cdr x))))

(define x (list 'a 'b))
(define y (list 'c 'd))
(define z (append x y))

z
; (a b c d)

(cdr x)
; (b)

(define w (append! x y))
; (last-pair x) gives (cons 'b nil)
; We set this pair's 2nd element to y, which is (cons 'c (cons 'd nil))
; So x is now '(a b c d)

w
; (a b c d)

(cdr x)
; (b c d)
