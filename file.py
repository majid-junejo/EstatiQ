import base64
import os
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from google import genai
import joblib
import numpy as np
import pandas as pd
from pydantic import BaseModel
import shap
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import NearestNeighbors
from sqlalchemy import Column, Float, Integer, JSON, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
import uvicorn

load_dotenv()

# ==========================================
# 1. DATABASE SETUP (MySQL)
# ==========================================
SQLALCHEMY_DATABASE_URL = (
    "mysql+pymysql://root:majidali%40123@localhost:3306/estatiq_db"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserDB(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, index=True)
  username = Column(String(50), unique=True, index=True)
  full_name = Column(String(100))
  phone = Column(String(50))
  city = Column(String(50))
  email = Column(String(100), unique=True)
  password = Column(String(100))


class PropertyDB(Base):
  __tablename__ = "properties"

  id = Column(Integer, primary_key=True, index=True)
  owner_username = Column(String(50))
  owner = Column(String(50))
  contact = Column(String(50))
  email = Column(String(100))
  purpose = Column(String(20))
  country = Column(String(50))
  city = Column(String(50))
  society = Column(String(100))
  area_sqft = Column(Float)
  bedrooms = Column(Integer)
  asking_price = Column(Float)
  lat = Column(Float, default=24.8607)
  lon = Column(Float, default=67.0011)
  status = Column(String(20), default="Available")

  images = Column(JSON, default=list)
  videos = Column(JSON, default=list)
  ratings = Column(JSON, default=list)
  comments = Column(JSON, default=list)


Base.metadata.create_all(bind=engine)


def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()


# ==========================================
# 2. ML MODEL & AI SETUP
# ==========================================
data = {
    "area_sqft": [500, 800, 1000, 1200, 1500, 1800, 2000, 2500],
    "bedrooms": [1, 2, 2, 3, 3, 4, 4, 5],
    "price": [
        2500000,
        4000000,
        5000000,
        6000000,
        7500000,
        9000000,
        10000000,
        12500000,
    ],
}
df = pd.DataFrame(data)

X = df[["area_sqft", "bedrooms"]]
y = df["price"]

from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(X, y)
joblib.dump(model, "model.pkl")

explainer = shap.Explainer(model, X)
gemini_api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None


def generate_insight(
    property_data: dict,
    predicted_price: float,
    top_features: dict,
    asking_price: Optional[float] = None,
) -> str:
  deal_eval = ""
  if asking_price:
    if asking_price <= predicted_price:
      deal_eval = f"Asking Price: Rs.{asking_price:,.0f} (Great Deal!)."
    else:
      deal_eval = f"Asking Price: Rs.{asking_price:,.0f} (Higher than model)."

  verdict = (
      " **Verdict: Good Deal ✅**"
      if asking_price and asking_price <= predicted_price * 1.05
      else " **Verdict: Overpriced ⚠️**"
  )

  if client is None:
    return (
        f"AI Insight Offline: Predicted market value is Rs.{predicted_price:,.0f}."
        f" {verdict}"
    )

  try:
    prompt = f"""You are an expert real estate analyst in Pakistan. 
Property specs: {property_data}
Predicted market value: Rs.{predicted_price:,.0f}
{deal_eval}
Top price-driving factors: {top_features}

Explain in 3 simple sentences why this property is priced this way, and at the end, give a clear verdict ('Verdict: Good Deal ✅' or 'Verdict: Overpriced ⚠️')."""

    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash"]
    response = None
    for m in models_to_try:
      try:
        response = client.models.generate_content(model=m, contents=prompt)
        break
      except Exception:
        continue

    if response and hasattr(response, "text"):
      return response.text
    else:
      return (
          f"AI Insight Fallback: Estimated market value is"
          f" Rs.{predicted_price:,.0f}.{verdict}"
      )
  except Exception as e:
    return (
        f"AI Insight Fallback: Estimated market value is"
        f" Rs.{predicted_price:,.0f}.{verdict}"
    )


# ==========================================
# 3. FASTAPI SETUP & ENDPOINTS
# ==========================================
app = FastAPI(title="EstatiQ API")


class UserSignupSchema(BaseModel):
  username: str
  full_name: str
  phone: str
  city: str
  email: str
  password: str


class UserLoginSchema(BaseModel):
  username: str
  password: str


class PropertyInput(BaseModel):
  area_sqft: float
  bedrooms: int
  asking_price: Optional[float] = None


class PropertyCreate(BaseModel):
  owner_username: str
  owner: str
  contact: str
  email: Optional[str] = None
  purpose: str
  country: str
  city: str
  society: str
  area_sqft: float
  bedrooms: int
  asking_price: float
  lat: float
  lon: float
  images: List[str] = []
  videos: List[str] = []


class CommentInput(BaseModel):
  name: str
  text: str


class RatingInput(BaseModel):
  rating: int


class HelpQuery(BaseModel):
  question: str


@app.post("/signup")
def signup(user: UserSignupSchema, db: Session = Depends(get_db)):
  existing = (
      db.query(UserDB)
      .filter(
          (UserDB.username == user.username) | (UserDB.email == user.email)
      )
      .first()
  )
  if existing:
    return {"error": "Username or Email already exists!"}
  new_user = UserDB(
      username=user.username,
      full_name=user.full_name,
      phone=user.phone,
      city=user.city,
      email=user.email,
      password=user.password,
  )
  db.add(new_user)
  db.commit()
  return {"message": "Signup successful!"}


@app.post("/signin")
def signin(user: UserLoginSchema, db: Session = Depends(get_db)):
  db_user = (
      db.query(UserDB)
      .filter(
          (UserDB.username == user.username)
          & (UserDB.password == user.password)
      )
      .first()
  )
  if db_user:
    return {
        "message": "Login successful",
        "username": db_user.username,
        "full_name": db_user.full_name,
    }
  return {"error": "Invalid username or password!"}


@app.get("/")
def home():
  return {"message": "EstatiQ API running 🚀"}


@app.get("/properties")
def get_properties(db: Session = Depends(get_db)):
  props = db.query(PropertyDB).all()
  props_dict = [p.__dict__ for p in props]

  if len(props_dict) >= 3:
    try:
      X_fraud = pd.DataFrame(
          [
              [p["area_sqft"], p["bedrooms"], p["asking_price"]]
              for p in props_dict
          ]
      )
      iso = IsolationForest(contamination=0.15, random_state=42)
      preds = iso.fit_predict(X_fraud)
      for i, p in enumerate(props_dict):
        p["is_suspicious"] = bool(preds[i] == -1)
    except Exception:
      for p in props_dict:
        p["is_suspicious"] = False
  else:
    for p in props_dict:
      p["is_suspicious"] = False

  return props_dict


@app.post("/recommendations/{prop_id}")
def get_recommendations(prop_id: int, db: Session = Depends(get_db)):
  props = db.query(PropertyDB).all()
  target = next((p for p in props if p.id == prop_id), None)
  if not target:
    return []

  other_props = [p for p in props if p.id != prop_id]
  if not other_props:
    return []

  try:
    X_all = pd.DataFrame(
        [
            [p.area_sqft, p.bedrooms, p.asking_price]
            for p in other_props
        ]
    )
    target_X = [[target.area_sqft, target.bedrooms, target.asking_price]]

    n_neighbors = min(3, len(other_props))
    nbrs = NearestNeighbors(n_neighbors=n_neighbors, algorithm="auto").fit(
        X_all
    )
    distances, indices = nbrs.kneighbors(target_X)

    recommended = [other_props[i] for i in indices[0]]
    return recommended
  except Exception:
    return other_props[:3]


@app.post("/add_property")
def add_property(prop: PropertyCreate, db: Session = Depends(get_db)):
  prop_data = (
      prop.model_dump() if hasattr(prop, "model_dump") else prop.dict()
  )
  new_prop = PropertyDB(**prop_data)
  db.add(new_prop)
  db.commit()
  db.refresh(new_prop)
  return {"message": "Property added successfully", "id": new_prop.id}


@app.post("/predict")
def predict_price(input_data: PropertyInput):
  input_df = pd.DataFrame(
      [[input_data.area_sqft, input_data.bedrooms]],
      columns=["area_sqft", "bedrooms"],
  )
  predicted_price = float(model.predict(input_df)[0])

  shap_values = explainer(input_df)
  vals = np.ravel(shap_values.values)
  top_features = {
      col: round(float(val), 2) for col, val in zip(input_df.columns, vals)
  }

  insight = generate_insight(
      {
          "area_sqft": input_data.area_sqft,
          "bedrooms": input_data.bedrooms,
      },
      predicted_price,
      top_features,
      input_data.asking_price,
  )
  return {
      "predicted_price": round(predicted_price, 2),
      "top_features": top_features,
      "ai_insight": insight,
  }


@app.post("/help_chat")
def help_chat(query: HelpQuery):
  q = query.question.lower()

  # Smart Instant Answers for App Features
  if "price insight" in q or "ai price" in q or "valuation" in q:
    return {
        "answer": (
            "The 🧠 AI Price Insight button is located on every property card"
            " inside the 'Explore Properties' tab! Click it to view the"
            " predicted market value and Gemini AI analysis."
        )
    }
  elif "list" in q or "sell" in q or "rent" in q or "post" in q:
    return {
        "answer": (
            "To list a property, go to the 'Post a New Listing' tab, fill in"
            " the location, media, specifications, and owner details, and click"
            " 'Publish Listing'."
        )
    }
  elif "fraud" in q or "suspicious" in q:
    return {
        "answer": (
            "EstatiQ uses an Isolation Forest machine learning model to"
            " automatically detect and flag unusual or outlier prices as 🚨 AI"
            " Fraud Alerts."
        )
    }
  elif "recommend" in q or "similar" in q:
    return {
        "answer": (
            "KNN Content-Based Filtering automatically suggests similar"
            " properties at the bottom of each property's ratings & comments"
            " section."
        )
    }

  # Fallback to Gemini if client is available
  if client is None:
    return {
        "answer": (
            f"EstatiQ Assistant: You asked about '{query.question}'. You can"
            " explore properties, check AI price insights on property cards, or"
            " post new listings!"
        )
    }
  try:
    prompt = f"""You are the official AI Support Assistant for EstatiQ, an advanced AI Real Estate Platform built for Pakistan. 
    User Question: {query.question}
    Provide a helpful, precise, and polite response."""
    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-flash"]
    response = None
    for m in models_to_try:
      try:
        response = client.models.generate_content(model=m, contents=prompt)
        break
      except Exception:
        continue
    if response and hasattr(response, "text"):
      return {"answer": response.text}
    else:
      return {
          "answer": (
              f"EstatiQ Assistant: I can help you explore properties, check AI"
              f" price insights, or post new listings!"
          )
      }
  except Exception as e:
    return {
        "answer": (
            f"EstatiQ Assistant: I can help you explore properties, check AI"
            f" price insights, or post new listings!"
        )
    }


@app.put("/mark_sold/{prop_id}")
def mark_sold(prop_id: int, db: Session = Depends(get_db)):
  prop = db.query(PropertyDB).filter(PropertyDB.id == prop_id).first()
  if prop:
    prop.status = "Sold/Rented"
    db.commit()
    return {"message": "Updated!"}
  return {"error": "Not found"}


@app.delete("/delete_property/{prop_id}")
def delete_property(prop_id: int, db: Session = Depends(get_db)):
  prop = db.query(PropertyDB).filter(PropertyDB.id == prop_id).first()
  if prop:
    db.delete(prop)
    db.commit()
    return {"message": "Property deleted successfully!"}
  return {"error": "Not found"}


@app.post("/add_comment/{prop_id}")
def add_comment(
    prop_id: int, comment: CommentInput, db: Session = Depends(get_db)
):
  prop = db.query(PropertyDB).filter(PropertyDB.id == prop_id).first()
  if prop:
    curr_comments = list(prop.comments) if prop.comments else []
    curr_comments.append(
        {"name": comment.name, "text": comment.text, "likes": 0}
    )
    prop.comments = curr_comments
    db.commit()
    return {"message": "Comment added!"}
  return {"error": "Not found"}


@app.put("/like_comment/{prop_id}/{c_index}")
def like_comment(
    prop_id: int, c_index: int, db: Session = Depends(get_db)
):
  prop = db.query(PropertyDB).filter(PropertyDB.id == prop_id).first()
  if prop and prop.comments and len(prop.comments) > c_index:
    curr_comments = list(prop.comments)
    curr_comments[c_index]["likes"] = (
        curr_comments[c_index].get("likes", 0) + 1
    )
    prop.comments = curr_comments
    db.commit()
    return {"message": "Liked!"}
  return {"error": "Not found"}


@app.post("/add_rating/{prop_id}")
def add_rating(
    prop_id: int, rating: RatingInput, db: Session = Depends(get_db)
):
  prop = db.query(PropertyDB).filter(PropertyDB.id == prop_id).first()
  if prop:
    curr_ratings = list(prop.ratings) if prop.ratings else []
    curr_ratings.append(rating.rating)
    prop.ratings = curr_ratings
    db.commit()
    return {"message": "Rating added!"}
  return {"error": "Not found"}


if __name__ == "__main__":
  uvicorn.run(app, host="127.0.0.1", port=8000)