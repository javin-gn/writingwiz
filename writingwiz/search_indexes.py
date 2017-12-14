import datetime
from haystack import indexes
from models import AstarcompoQuestions

class QuestionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    questionid = indexes.CharField(model_attr='questionid')
    question = indexes.CharField(model_attr='question')
    category = indexes.CharField(model_attr='questionCategory')
    stype = indexes.CharField(model_attr='questionType')

    def get_model(self):
        return AstarcompoQuestions 

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()
        
