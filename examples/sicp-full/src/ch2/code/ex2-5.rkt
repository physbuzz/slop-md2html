#lang sicp
(define (pow n m) (if (< m 1) 1 (* n (pow n (- m 1)))))

;; Find how many powers of two the number has
;; Might be fun to optimize once I know more scheme.
(define (npowers base n)
  (define (npowers-iter product k)
    (if (= (gcd product n) product) 
      (npowers-iter (* product base) (+ k 1))
      k))
  (npowers-iter base 0))
(define (cons a b) (* (pow 2 a) (pow 3 b)))
(define (car z) (npowers 2 z))
(define (cdr z) (npowers 3 z))

(let ((arg (cons 10 13)))
  (display "2^a 3^b is: ") (display arg) (newline)
  (display "a is: ") (display (car arg)) (newline)
  (display "b is: ") (display (cdr arg)) (newline))
