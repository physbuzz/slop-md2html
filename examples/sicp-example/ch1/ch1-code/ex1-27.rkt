#lang sicp

(define (square n) (* n n))

(define (expmod base exp m)
  (cond ((= exp 0) 1)
        ((even? exp)
         (remainder
          (square (expmod base (/ exp 2) m))
          m))
        (else
         (remainder
          (* base (expmod base (- exp 1) m))
          m))))

(define (test-all-iter n test bool)
  (if (= n test) 
    bool
    (test-all-iter n 
              (+ test 1) 
              (and bool (= (expmod test n n) test)))))
(define (carm-test n)
  (display "Fermat test of ")
  (display n)
  (display " : ")
  (display (test-all-iter n 2 #t))
  (newline))

(display "Testing some non-carmichael non-primes") (newline)
(carm-test 231)
(carm-test 1419)
(carm-test 2001)
(carm-test 8631)
(newline) (display "Testing some carmichael non-primes") (newline)
(carm-test 561)
(carm-test 1105)
(carm-test 1729)
(carm-test 2465)
(carm-test 2821)
(carm-test 6601)
