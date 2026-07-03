#lang sicp

(define (variable? x) (symbol? x))
(define (same-variable? v1 v2)
  (and (variable? v1)
       (variable? v2)
       (eq? v1 v2)))

(define (numorvar? x) (or (variable? x) (number? x)))

(define (make-sum a1 a2)
  (cond ((=number? a1 0) a2)
        ((=number? a2 0) a1)
        ((and (number? a1) (number? a2))
         (+ a1 a2))
        (else (list a1 '+ a2))))
(define (make-product m1 m2)
  (cond ((or (=number? m1 0)
             (=number? m2 0))
         0)
        ((=number? m1 1) m2)
        ((=number? m2 1) m1)
        ((and (number? m1) (number? m2))
         (* m1 m2))
        (else (list m1 '* m2))))
(define (=number? exp num)
  (and (number? exp) (= exp num)))

(define (sum? x)
  (and (pair? x) (eq? (cadr x) '+)))
(define (addend s) (car s))
(define (augend s) (caddr s)) 

(define (product? x)
  (and (pair? x) (eq? (cadr x) '*)))
(define (multiplier p) (car p))
(define (multiplicand p) (caddr p))

(define (deriv exp var)
  (cond ((number? exp) 0)
        ((variable? exp)
         (if (same-variable? exp var) 1 0))
        ((sum? exp)
         (make-sum (deriv (addend exp) var)
                   (deriv (augend exp) var)))
        ((product? exp)
         (make-sum
          (make-product
           (multiplier exp)
           (deriv (multiplicand exp) var))
          (make-product
           (deriv (multiplier exp) var)
           (multiplicand exp))))
        (else (error "unknown expression
                      type: DERIV" exp))))

(newline) (display "make-product tests") (newline)
(make-product 'x 'y)
(make-product 'x (make-product 'y 'z))
(make-product 4 (make-product 2 'x))
(make-product (make-product 'a 'x) (make-product 2 'x))

(newline) (display "make-sum tests") (newline)
(make-sum 'x 'y)
(make-sum 'x (make-sum 'y 'z))
(make-sum 4 (make-sum 2 'x))
(make-sum (make-sum 'a 'x) (make-sum 2 'x))

(newline) (display "deriv and make-product tests") (newline)
(deriv (make-product 'x 'y) 'x)
(deriv (make-product 'x (make-product 'y 'z)) 'x)
(deriv (make-product 4 (make-product 2 'x)) 'x)
(deriv (make-product (make-product 'a 'x) (make-product 2 'x)) 'x)

(newline) (display "sum and make-sum tests") (newline)
(deriv (make-sum 'x 'y) 'x)
(deriv (make-sum 'x (make-sum 'y 'z)) 'x)
(deriv (make-sum 4 (make-sum 2 'x)) 'x)
(deriv (make-sum (make-sum 'a 'x) (make-sum 2 'x)) 'x)
