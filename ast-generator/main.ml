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
  | LogicalAnd of expr * expr
  | LogicalOr of expr * expr
  | Not of expr

  (* Bitwise Operators *)
  | BitwiseAnd of expr * expr
  | BitwiseOr of expr * expr
  | BitwiseComplement of expr
  | BitwiseXor of expr * expr
  | LeftShift of expr * expr
  | RightShift of expr * expr

  (* Constants and Variables *)
  | Variable of string
  | Int of int