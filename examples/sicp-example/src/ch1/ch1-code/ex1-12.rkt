#lang sicp

(define (choose n m)
  (if (or (< m 1) (> m (- n 1)))
    1
    (+ (choose (- n 1) m)
       (choose (- n 1) (- m 1)))))

(define (print-n char n) 
  (display char)
  (if (> n 1) (print-n char (- n 1))))

(define (print-binom-seq n m) 
  (display (choose n m))
  (display " ")
  (if (< m n) (print-binom-seq n (+ m 1))))

(define (print-pascal-line n middle)
  (print-n " " (- middle n))
  (print-binom-seq n 0)
  (newline))

(define (print-pascal-triangle n)
  (define (print-pascal-loop nprime middle)
    (print-pascal-line nprime middle)
    (if (< nprime n) (print-pascal-loop (+ nprime 1) middle)))
  (print-pascal-loop 0 (+ n 1)))

(print-pascal-triangle 6)

