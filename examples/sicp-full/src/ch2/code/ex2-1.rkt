#lang sicp

(define (make-rat n d)
  (if (< d 0) (make-rat (- n) (- d))
    (let ((g (gcd n d)))
      (cons (/ n g) 
            (/ d g)))))

(make-rat 10 15)
(make-rat 10 -15)
(make-rat -10 15)
(make-rat -10 -15)
