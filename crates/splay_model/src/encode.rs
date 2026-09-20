//! Canonical shape grammar: EMPTY = `.`, NODE = `(LEFT RIGHT)`.
//! tree_id follows raw-ASCII lexicographic sort of shape codes.

#[derive(Clone, PartialEq, Eq, Debug)]
pub enum Shape {
    Empty,
    Node(Box<Shape>, Box<Shape>),
}

#[derive(Debug, PartialEq, Eq)]
pub struct ParseError(pub String);

pub fn parse_shape(s: &str) -> Result<Shape, ParseError> {
    let bytes = s.as_bytes();
    let (node, i) = parse_at(bytes, 0)?;
    if i != bytes.len() {
        return Err(ParseError("trailing characters".to_string()));
    }
    Ok(node)
}

fn parse_at(bytes: &[u8], i: usize) -> Result<(Shape, usize), ParseError> {
    match bytes.get(i) {
        Some(b'.') => Ok((Shape::Empty, i + 1)),
        Some(b'(') => {
            let (left, j) = parse_at(bytes, i + 1)?;
            let (right, k) = parse_at(bytes, j)?;
            match bytes.get(k) {
                Some(b')') => Ok((Shape::Node(Box::new(left), Box::new(right)), k + 1)),
                _ => Err(ParseError(format!("expected ')' at {k}"))),
            }
        }
        _ => Err(ParseError(format!("bad character at {i}"))),
    }
}

pub fn serialize_shape(shape: &Shape) -> String {
    match shape {
        Shape::Empty => ".".to_string(),
        Shape::Node(l, r) => format!("({}{})", serialize_shape(l), serialize_shape(r)),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn round_trip_known_shapes() {
        for code in [".", "(..)", "((..).)", "(.(..))", "((..)(..))", "(((..).).)"] {
            assert_eq!(serialize_shape(&parse_shape(code).unwrap()), code);
        }
    }

    #[test]
    fn rejects_malformed() {
        assert!(parse_shape("(()").is_err());
        assert!(parse_shape("(..)..").is_err());
        assert!(parse_shape("").is_err());
    }
}
