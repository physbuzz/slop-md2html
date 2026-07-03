#lang sicp

(define RAND-MAX 2147483647)

(define (random-float low high)
  (let ((range (- high low)))
    (+ low (* range (/ (* 1.0 (random RAND-MAX) ) RAND-MAX)))))

(define (estimate-integral P x1 x2 y1 y2 ntrials)
  (define (e-inner n estimate)
    (if (< n 1) 
      estimate
      (e-inner (- n 1) 
               (+ estimate (if (P (random-float x1 x2)
                      (random-float y1 y2)) 1 0)))))
  (* (/ (* 1.0 (e-inner ntrials 0)) ntrials)
     (- x2 x1)
     (- y2 y1)))


(define (square x) (* x x))
(estimate-integral 
  (lambda (x y) (< (+ (square x) (square y)) 1))
  -1 1 -1 1 1000000)
