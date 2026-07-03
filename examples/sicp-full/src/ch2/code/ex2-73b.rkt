
#lang sicp

(define operation-table '())

(define (assoc key records)
  (cond ((null? records) #f)
        ((equal? key (caar records)) (car records))
        (else (assoc key (cdr records)))))

(define (assoc-op key records)
   (cond ((null? records) #f)
         ((equal? key (caar records)) (car records))
         (else (assoc-op key (cdr records)))))

(define (put op type-tags proc)
  (let ((op-list-entry (assoc-op op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
           (let ((proc-pair-entry (assoc type-tags proc-list)))
             (if proc-pair-entry
                 (set-cdr! proc-pair-entry proc)
                 (set-car! (cdr op-list-entry)
                           (cons (cons type-tags proc) proc-list)))))
        (set! operation-table
              (cons (list op (list (cons type-tags proc)))
                    operation-table)))))

(define (get op type-tags)
  (let ((op-list-entry (assoc-op op operation-table)))
    (if op-list-entry
        (let ((proc-list (cadr op-list-entry)))
          (let ((proc-pair-entry (assoc type-tags proc-list)))
            (if proc-pair-entry
                (cdr proc-pair-entry)
                #f)))
        #f)))


(define (variable? x) (symbol? x))
(define (same-variable? v1 v2)
  (and (variable? v1)
       (variable? v2)
       (eq? v1 v2)))

(define (make-sum a1 a2)
  (cond ((=number? a1 0) a2)
        ((=number? a2 0) a1)
        ((and (number? a1) (number? a2))
         (+ a1 a2))
        (else (list '+ a1 a2))))
(define (make-product m1 m2)
  (cond ((or (=number? m1 0)
             (=number? m2 0))
         0)
        ((=number? m1 1) m2)
        ((=number? m2 1) m1)
        ((and (number? m1) (number? m2))
         (* m1 m2))
        (else (list '* m1 m2))))
(define (=number? exp num)
  (and (number? exp) (= exp num)))

(define (sum? x)
  (and (pair? x) (eq? (car x) '+)))
(define (addend s) (cadr s))
(define (augend s) (caddr s))

(define (product? x)
  (and (pair? x) (eq? (car x) '*)))
(define (multiplier p) (cadr p))
(define (multiplicand p) (caddr p))

(define (exponentiation? x)
  (and (pair? x) (eq? (car x) '**)))
(define (base x) (cadr x))
(define (exponent x) (caddr x))
(define (make-exponentiation a b)
  (cond ((=number? b 0) 1)
        ((=number? b 1) a)
        ((=number? a 0) 0)
        (else (list '** a b))))

(define (operator exp) (car exp))
(define (operands exp) (cdr exp))
(define (deriv exp var)
  (cond ((number? exp) 0)
        ((variable? exp)
          (if (same-variable? exp var)
              1
              0))
        (else ((get (operator exp) 'deriv)
               exp
               var))))

(put '+ 'deriv 
  (lambda (exp var) 
    (make-sum (deriv (addend exp) var)
              (deriv (augend exp) var))))

(put '* 'deriv 
  (lambda (exp var) 
    (make-sum
     (make-product
      (multiplier exp)
      (deriv (multiplicand exp) var))
     (make-product
      (deriv (multiplier exp) var)
      (multiplicand exp)))))
(put '** 'deriv 
  (lambda (exp var) 
    (make-product
     (make-product
      (exponent exp)
      (make-exponentiation (base exp) (make-sum (exponent exp) -1)))
     (deriv (base exp) var))))

(deriv (make-exponentiation 'x 3) 'x)
(deriv (make-exponentiation 'x 2) 'x)
(deriv (make-exponentiation 'x 1) 'x)

;;d((y*(x+2))**2)/dx = 2y**2 * (x+2)
(deriv (make-exponentiation (make-product 'y (make-sum 'x 2)) 2) 'x)




