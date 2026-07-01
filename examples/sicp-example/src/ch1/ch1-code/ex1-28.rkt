#lang sicp

(define (square n) (* n n))

; In the context of our prime test, base is `a` (the randomly chosen test)
; exp is n (The potential prime), and m is also n.
; Consider the piece of code:
;         (remainder
;          (square (expmod base (/ exp 2) m))
;          m))
; Normally I'd want to do something like
; result = (expmod base (/ exp 2) m)
; if(result*result%m == 1 && result !=1 && result != m-1)
;   return 0;
; else
;   return result*result%m
(define (expmod-fancy base exp m)
  ; Kinda silly to evaluate remainder square result twice, but whatever.
  (define (even-function result)
    (if 
      (and (= (remainder (square result) m) 1)
           (not (= result 1))
           (not (= result (- m 1))))
      0
      ; if result is zero, it'll be passed through
      (remainder (square result) m)))   
  (cond ((= exp 0) 1)
        ((even? exp)
         (even-function (expmod-fancy base (/ exp 2) m)))
        (else
         ; here, if expmod-fancy returns 0, it's passed through also.
         (remainder
          (* base (expmod-fancy base (- exp 1) m))
          m))))

(define (fermat-test n)
  (define (try-it a)
    (= (expmod-fancy a (- n 1) n) 1))
  (try-it (+ 1 (random (- n 1)))))

(define (miller-rabin-prime? n times)
  (cond ((= times 0) true)
        ((fermat-test n)
         (miller-rabin-prime? n (- times 1)))
        (else false)))

(define (mrtest n)
  (display "Miller-Rabin test of ")
  (display n)
  (display " : ")
  (display (miller-rabin-prime? n 1))
  (newline))

(display "Testing some non-carmichael non-primes") (newline)
(mrtest 231)
(mrtest 1419)
(mrtest 2001)
(mrtest 8631)
(newline) (display "Testing some carmichael non-primes") (newline)
(mrtest 561)
(mrtest 1105)
(mrtest 1729)
(mrtest 2465)
(mrtest 2821)
(mrtest 6601)
(newline) (display "Testing some primes") (newline)
(mrtest 1297)
(mrtest 1579)
(mrtest 2671)
(mrtest 6199)
(mrtest 7013)
