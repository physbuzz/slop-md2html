#lang sicp

(define pi 3.14159)
(define (square x) (* x x))
(define (accumulate op initial sequence)
  (if (null? sequence)
      initial
      (op (car sequence)
          (accumulate op
                      initial
                      (cdr sequence)))))
;; get and put definitions
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

;; Modified for ex2-78. 
(define (attach-tag type-tag contents)
  (if (equal? type-tag 'scheme-number) 
      contents
      (cons type-tag contents)))
(define (type-tag datum)
  (cond ((pair? datum) (car datum))
        ((number? datum) 'scheme-number)
        (else (error "Bad tagged datum: TYPE-TAG" datum))))
(define (contents datum)
  (cond ((pair? datum) (cdr datum))
        ((number? datum) datum)
        (else (error "Bad tagged datum: CONTENTS" datum))))
(define (apply-generic op . args)
  (let ((type-tags (map type-tag args)))
    (let ((proc (get op type-tags)))
      (if proc
          (apply proc (map contents args))
          (error
            "No method for these types: APPLY-GENERIC"
            (list op type-tags))))))


;; Number package
(define (install-scheme-number-package)
  (define (tag x)
    (attach-tag 'scheme-number x))
  (put 'add '(scheme-number scheme-number)
       (lambda (x y) (tag (+ x y))))
  (put 'sub '(scheme-number scheme-number)
       (lambda (x y) (tag (- x y))))
  (put 'mul '(scheme-number scheme-number)
       (lambda (x y) (tag (* x y))))
  (put 'div '(scheme-number scheme-number)
       (lambda (x y) (tag (/ x y))))
  (put 'make 'scheme-number
       (lambda (x) (tag x)))
  (put '=zero? '(scheme-number)
       (lambda (x) (= x 0)))
  (put 'negate '(scheme-number)
       (lambda (x) (- x)))
  'done)

(install-scheme-number-package)

(define (make-scheme-number n)
  ((get 'make 'scheme-number) n))

;; ===================================================================
;; ======================== Rational package =========================
;; ===================================================================

(define (install-rational-package)
  ;; internal procedures
  (define (numer x) (car x))
  (define (denom x) (cdr x))
  (define (make-rat n d)
    (let ((g (gcd n d)))
      (cons (/ n g) (/ d g))))
  (define (add-rat x y)
    (make-rat (+ (* (numer x) (denom y))
                 (* (numer y) (denom x)))
              (* (denom x) (denom y))))
  (define (sub-rat x y)
    (make-rat (- (* (numer x) (denom y))
                 (* (numer y) (denom x)))
              (* (denom x) (denom y))))
  (define (mul-rat x y)
    (make-rat (* (numer x) (numer y))
              (* (denom x) (denom y))))
  (define (div-rat x y)
    (make-rat (* (numer x) (denom y))
              (* (denom x) (numer y))))

  ;; z1a/z1b = z2a/z2b  iff z1a*z2b - z2a*z1b = 0
  ;; equ? for problem 2.79
  (define (equ? z1 z2)
    (= (- (* (numer z1) (denom z2))
          (* (numer z2) (denom z1)))
        0))
  ;; interface to rest of the system
  (put 'equ? '(rational rational) equ?)
  (define (tag x) (attach-tag 'rational x))
  (put 'add '(rational rational)
       (lambda (x y) (tag (add-rat x y))))
  (put 'sub '(rational rational)
       (lambda (x y) (tag (sub-rat x y))))
  (put 'mul '(rational rational)
       (lambda (x y) (tag (mul-rat x y))))
  (put 'div '(rational rational)
       (lambda (x y) (tag (div-rat x y))))
  (put 'make 'rational
       (lambda (n d) (tag (make-rat n d))))
  ;problem 2.80
  (put '=zero? '(rational)
    (lambda (a) (= (numer a) 0)))
  (put 'negate '(rational)
       (lambda (r) (tag (make-rat (- (numer r)) (denom r)))))
  'done)

(install-rational-package)

(define (make-rational n d)
  ((get 'make 'rational) n d))

;; ===================================================================
;; ================= Complex polar and rectangular ===================
;; ===================================================================

(define (install-polar-package)
  ;; internal procedures
  (define (magnitude z) (car z))
  (define (angle z) (cdr z))
  (define (make-from-mag-ang r a) (cons r a))
  (define (real-part z)
    (* (magnitude z) (cos (angle z))))
  (define (imag-part z)
    (* (magnitude z) (sin (angle z))))
  (define (make-from-real-imag x y)
    (cons (sqrt (+ (square x) (square y)))
          (atan y x)))
  ;; interface to the rest of the system
  (define (tag x) (attach-tag 'polar x))
  (put 'real-part '(polar) real-part)
  (put 'imag-part '(polar) imag-part)
  (put 'magnitude '(polar) magnitude)
  (put 'angle '(polar) angle)
  (put 'make-from-real-imag 'polar
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'polar
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  (put 'negate '(polar)
       (lambda (z) (tag (make-from-mag-ang (magnitude z) (+ (angle z) pi)))))
  'done)
(install-polar-package)

(define (install-rectangular-package)
  ;; internal procedures
  (define (real-part z) (car z))
  (define (imag-part z) (cdr z))
  (define (make-from-real-imag x y)
    (cons x y))
  (define (magnitude z)
    (sqrt (+ (square (real-part z))
             (square (imag-part z)))))
  (define (angle z)
    (atan (imag-part z) (real-part z)))
  (define (make-from-mag-ang r a)
    (cons (* r (cos a)) (* r (sin a))))
  ;; interface to the rest of the system
  (define (tag x)
    (attach-tag 'rectangular x))
  (put 'real-part '(rectangular) real-part)
  (put 'imag-part '(rectangular) imag-part)
  (put 'magnitude '(rectangular) magnitude)
  (put 'angle '(rectangular) angle)
  (put 'make-from-real-imag 'rectangular
       (lambda (x y)
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'rectangular
       (lambda (r a)
         (tag (make-from-mag-ang r a))))
  (put 'negate '(rectangular)
       (lambda (z) (tag (make-from-real-imag (- (real-part z) (- (imag-part z)))))))
  'done)
(install-rectangular-package)

;; ===================================================================
;; ========================= Complex package =========================
;; ===================================================================

(define (install-complex-package)
  ;; imported procedures from rectangular 
  ;; and polar packages
  (define (real-part z)
    (apply-generic 'real-part z))
  (define (imag-part z)
    (apply-generic 'imag-part z))
  (define (magnitude z)
    (apply-generic 'magnitude z))
  (define (angle z)
    (apply-generic 'angle z))

  (define (make-from-real-imag x y)
    ((get 'make-from-real-imag 
          'rectangular) 
     x y))
  (define (make-from-mag-ang r a)
    ((get 'make-from-mag-ang 'polar) 
     r a))
  ;; internal procedures
  (define (add-complex z1 z2)
    (make-from-real-imag 
     (+ (real-part z1) (real-part z2))
     (+ (imag-part z1) (imag-part z2))))
  (define (sub-complex z1 z2)
    (make-from-real-imag 
     (- (real-part z1) (real-part z2))
     (- (imag-part z1) (imag-part z2))))
  (define (mul-complex z1 z2)
    (make-from-mag-ang 
     (* (magnitude z1) (magnitude z2))
     (+ (angle z1) (angle z2))))
  (define (div-complex z1 z2)
    (make-from-mag-ang 
     (/ (magnitude z1) (magnitude z2))
     (- (angle z1) (angle z2))))

  (define (equ? z1 z2) ; for problem 2.79
    (and (= (real-part z1) (real-part z2)) 
         (= (imag-part z1) (imag-part z2))))
  ;; interface to rest of the system
  (put 'equ? '(complex complex) equ?)
  (put 'real-part '(complex) real-part) ; Changes from problem 2.77
  (put 'imag-part '(complex) imag-part)
  (put 'magnitude '(complex) magnitude)
  (put 'angle '(complex) angle)
  (put 'negate '(complex)
       (lambda (z) (tag (apply-generic 'negate z))))

  (define (tag z) (attach-tag 'complex z))
  (put 'add '(complex complex)
       (lambda (z1 z2) 
         (tag (add-complex z1 z2))))
  (put 'sub '(complex complex)
       (lambda (z1 z2) 
         (tag (sub-complex z1 z2))))
  (put 'mul '(complex complex)
       (lambda (z1 z2) 
         (tag (mul-complex z1 z2))))
  (put 'div '(complex complex)
       (lambda (z1 z2) 
         (tag (div-complex z1 z2))))
  (put 'make-from-real-imag 'complex
       (lambda (x y) 
         (tag (make-from-real-imag x y))))
  (put 'make-from-mag-ang 'complex
       (lambda (r a) 
         (tag (make-from-mag-ang r a))))
  ;problem 2.80
  (put '=zero? '(complex)
    (lambda (z) (and (= (real-part z) 0) (= (imag-part z) 0))))
  'done)

(install-complex-package)

(define (=zero? a)
  (apply-generic '=zero? a))
(define (real-part z)
  (apply-generic 'real-part z))
(define (imag-part z)
  (apply-generic 'imag-part z))
(define (magnitude z)
  (apply-generic 'magnitude z))
(define (angle z)
  (apply-generic 'angle z))
(define (mul a b)
  (apply-generic 'mul a b))
(define (add a b)
  (apply-generic 'add a b))
(define (sub a b)
  (apply-generic 'sub a b))
(define (equ? a b)
  (apply-generic 'equ? a b))


(define (install-polynomial-package)
  ;; internal procedures
  ;; representation of poly
  (define (make-poly variable term-list)
    (cons variable term-list))
  (define (variable p) (car p))
  (define (term-list p) (cdr p))

  (define (variable? x) (symbol? x))
  (define (same-variable? v1 v2)
    (and (variable? v1)
         (variable? v2)
         (eq? v1 v2)))

  (define (mul-terms L1 L2)
    (if (empty-termlist? L1)
      (the-empty-termlist)
      (add-terms
       (mul-term-by-all-terms
        (first-term L1) L2)
       (mul-terms (rest-terms L1) L2))))

  (define (mul-term-by-all-terms t1 L)
    (if (empty-termlist? L)
      (the-empty-termlist)
      (let ((t2 (first-term L)))
        (adjoin-term
         (make-term
          (+ (order t1) (order t2))
          (mul (coeff t1) (coeff t2)))
         (mul-term-by-all-terms
          t1
          (rest-terms L))))))


  ;; representation of terms and term lists
  (define (adjoin-term term term-list)
    (if (=zero? (coeff term))
      term-list
      (cons term term-list)))
  (define (the-empty-termlist) '())
  (define (first-term term-list) (car term-list))
  (define (rest-terms term-list) (cdr term-list))
  (define (empty-termlist? term-list)
    (null? term-list))
  (define (make-term order coeff)
    (list order coeff))
  (define (order term) (car term))
  (define (coeff term) (cadr term))


  (define (add-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (make-poly
       (variable p1)
       (add-terms (term-list p1)
                  (term-list p2)))
      (error "Polys not in same var:
             ADD-POLY"
             (list p1 p2))))

  (define (mul-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (make-poly
       (variable p1)
       (mul-terms (term-list p1)
                  (term-list p2)))
      (error "Polys not in same var:
             MUL-POLY"
             (list p1 p2))))

  (define (add-terms L1 L2)
    (cond ((empty-termlist? L1) L2)
      ((empty-termlist? L2) L1)
      (else
       (let ((t1 (first-term L1))
             (t2 (first-term L2)))
         (cond ((> (order t1) (order t2))
                (adjoin-term
                 t1
                 (add-terms (rest-terms L1)
                            L2)))
           ((< (order t1) (order t2))
            (adjoin-term
             t2
             (add-terms
              L1
              (rest-terms L2))))
           (else
            (adjoin-term
             (make-term
              (order t1)
              (add (coeff t1)
                   (coeff t2)))
             (add-terms
              (rest-terms L1)
              (rest-terms L2)))))))))

;; (ct1 x^(ot1)+rest1)/(ct2 x^(ot2)+rest2) 
;; =(poly1 - (ct1/ct2) x^(ot1-ot2)(poly2) + (ct1/ct2) x^(ot1-ot2)(poly2))/(poly2)
;; =(ct1/ct2) x^(ot1-ot2) + (poly1 - (ct1/ct2) x^(ot1-ot2)(poly2))/poly2


  ;; During construction, we don't check whether coefficients are zero
  ;; So now, we have to check all coefficients.
  (define (=zero?-poly poly)
    (accumulate (lambda (x y) (and y (=zero? (coeff x))))
                #t
                (term-list poly)))
  ;; Make sure to install the function
  (put '=zero? '(polynomial) =zero?-poly)

  ;; Exercise 2-88
  (define (negate-terms L) 
    (if (empty-termlist? L)
      L
      (let ((t (first-term L)) (r (rest-terms L)))
        (adjoin-term (make-term (order t) (apply-generic 'negate (coeff t)))
                     (negate-terms r)))))
  (define (sub-terms L1 L2)
    (add-terms L1 (negate-terms L2)))
  (define (sub-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (make-poly
       (variable p1)
       (sub-terms (term-list p1)
                  (term-list p2)))
      (error "Polys not in same var:
             SUB-POLY"
             (list p1 p2))))
  (define (div-terms L1 L2)
    (if (empty-termlist? L1)
        (list (the-empty-termlist) 
              (the-empty-termlist))
        (let ((t1 (first-term L1))
              (t2 (first-term L2)))
          (if (> (order t2) (order t1))
              (list (the-empty-termlist) L1)
              (let ((new-c (apply-generic 'div (coeff t1) 
                                               (coeff t2)))
                    (new-o (- (order t1) 
                              (order t2))))
                (let ((new-t (make-term new-o new-c)))
                  (let ((rest-of-result
                         (div-terms 
                           (sub-terms L1 (mul-term-by-all-terms new-t L2)) 
                           L2)))
                    (let ((div-val (car rest-of-result))
                          (rem-val (cadr rest-of-result)))
                      (list (add-terms (list new-t) div-val)
                            rem-val)))))))))
  (put 'sub '(polynomial polynomial)
       (lambda (p1 p2) 
         (tag (sub-poly p1 p2))))




  (define (div-poly p1 p2)
    (if (same-variable? (variable p1)
                        (variable p2))
      (let ((res (div-terms (term-list p1)
                  (term-list p2))))
         (list (make-poly (variable p1) (car res)) (make-poly (variable p1) (cadr res))))
      (error "Polys not in same var:
             SUB-POLY"
             (list p1 p2))))

  (define (poly-remainder p1 p2)
    (cadr (div-poly p1 p2)))
  (define (poly-gcd a b)
    (if (=zero?-poly b)
        a
        (poly-gcd b (poly-remainder a b))))

  (put 'remainder '(polynomial polynomial) 
       (lambda (p1 p2)
         (tag (poly-remainder p1 p2))))
  (put 'gcd '(polynomial polynomial) 
       (lambda (p1 p2)
         (tag (poly-gcd p1 p2))))

  (put 'div-poly '(polynomial polynomial) 
       (lambda (p1 p2)
         (let ((res (div-poly p1 p2)))
           (list (tag (car res)) (tag (cadr res))))))
  (put 'negate '(polynomial)
       (lambda (p) 
         (tag (make-poly (variable p) (negate-terms (term-list p))))))
  ;; interface to rest of the system
  (define (tag p) (attach-tag 'polynomial p))
  (put 'add '(polynomial polynomial)
       (lambda (p1 p2) 
         (tag (add-poly p1 p2))))
  (put 'mul '(polynomial polynomial)
       (lambda (p1 p2) 
         (tag (mul-poly p1 p2))))
  (put 'make 'polynomial
       (lambda (var terms) 
         (tag (make-poly var terms))))
  'done)

(install-polynomial-package)

(define (make-polynomial var terms)
  ((get 'make 'polynomial) var terms))

(define p1
  (make-polynomial
   'x '((2 1) (1 -2) (0 1))))
(define p2
  (make-polynomial
   'x '((2 11) (0 7))))
(define p3
  (make-polynomial
   'x '((1 13) (0 5))))
(define q1
  (apply-generic 'mul p1 p2))
(define q2
  (apply-generic 'mul p1 p3))

(apply-generic 'gcd q1 q2)
