type expr =
  (* Arithmetic *)
  | Neg of expr
  | Plus of expr * expr
  | Minus of expr * expr
  | Times of expr * expr
  | Div of expr * expr
  | Mod of expr * expr
  | LessThan of expr * expr
  | LessEqual of expr * expr
  | GreaterThan of expr * expr
  | GreaterEqual of expr * expr
  | Equal of expr * expr
  | NotEqual of expr * expr

  (* Logical Operators *)
  | Not of expr

  (* Bitwise Operators *)
  | BitwiseAnd of expr * expr
  | BitwiseOr of expr * expr
  | BitwiseComplement of expr
  | BitwiseXor of expr * expr
  | LeftShift of expr * expr
  | RightShift of expr * expr

  (* Constants and Variables *)
  | X
  | Y
  | IntLit of int

let rec string_of_expr = function 
  | Neg(e) -> "(-" ^ string_of_expr e ^ ")"
  | Plus(e1, e2) -> "(" ^ string_of_expr e1 ^ " + " ^ string_of_expr e2 ^ ")"
  | Minus(e1, e2) -> "(" ^ string_of_expr e1 ^ " - " ^ string_of_expr e2 ^ ")"
  | Times(e1, e2) -> "(" ^ string_of_expr e1 ^ " * " ^ string_of_expr e2 ^ ")"
  | Div(e1, e2) -> "(" ^ string_of_expr e1 ^ " / " ^ string_of_expr e2 ^ ")"
  | Mod(e1, e2) -> "(" ^ string_of_expr e1 ^ " % " ^ string_of_expr e2 ^ ")"
  | LessThan(e1, e2) -> "(" ^ string_of_expr e1 ^ " < " ^ string_of_expr e2 ^ ")"
  | LessEqual(e1, e2) -> "(" ^ string_of_expr e1 ^ " <= " ^ string_of_expr e2 ^ ")"
  | GreaterThan(e1, e2) -> "(" ^ string_of_expr e1 ^ " > " ^ string_of_expr e2 ^ ")"
  | GreaterEqual(e1, e2) -> "(" ^ string_of_expr e1 ^ " >= " ^ string_of_expr e2 ^ ")"
  | Equal(e1, e2) -> "(" ^ string_of_expr e1 ^ " == " ^ string_of_expr e2 ^ ")"
  | NotEqual(e1, e2) -> "(" ^ string_of_expr e1 ^ " != " ^ string_of_expr e2 ^ ")"

  | Not(e) -> "(!" ^ string_of_expr e ^ ")"

  | BitwiseAnd(e1, e2) -> "(" ^ string_of_expr e1 ^ " & " ^ string_of_expr e2 ^ ")"
  | BitwiseOr(e1, e2) -> "(" ^ string_of_expr e1 ^ " | " ^ string_of_expr e2 ^ ")"
  | BitwiseComplement(e) -> "(~" ^ string_of_expr e ^ ")"
  | BitwiseXor(e1, e2) -> "(" ^ string_of_expr e1 ^ " ^ " ^ string_of_expr e2 ^ ")"
  | LeftShift(e1, e2) -> "(" ^ string_of_expr e1 ^ " << " ^ string_of_expr e2 ^ ")"
  | RightShift(e1, e2) -> "(" ^ string_of_expr e1 ^ " >> " ^ string_of_expr e2 ^ ")"

  | X -> "x"
  | Y -> "y"
  | IntLit(i) -> string_of_int i

