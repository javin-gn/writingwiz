from django.contrib import admin

from .models import (
    Questions, ModelAns, Pictorial, LearningVideo,
    VpCategory, Vocabulary, Phrase, UserProfile,
)


class ModelAnsInline(admin.TabularInline):
    model = ModelAns
    extra = 1
    fields = ('ansid', 'ans')


class PictorialInline(admin.TabularInline):
    model = Pictorial
    extra = 1
    fields = ('picid', 'url')


@admin.register(Questions)
class QuestionsAdmin(admin.ModelAdmin):
    list_display = ('questionid', 'questionType', 'questionCategory', 'short_question')
    list_filter = ('questionType', 'questionCategory')
    search_fields = ('question', 'questionCategory')
    inlines = [ModelAnsInline, PictorialInline]

    def short_question(self, obj):
        return obj.question[:80]
    short_question.short_description = 'Question'


@admin.register(ModelAns)
class ModelAnsAdmin(admin.ModelAdmin):
    list_display = ('ansid', 'questionid', 'short_ans')
    search_fields = ('ans',)
    autocomplete_fields = ('questionid',)

    def short_ans(self, obj):
        return obj.ans[:80]
    short_ans.short_description = 'Answer'


@admin.register(Pictorial)
class PictorialAdmin(admin.ModelAdmin):
    list_display = ('picid', 'questionid', 'url')
    autocomplete_fields = ('questionid',)


@admin.register(LearningVideo)
class LearningVideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'url', 'noOfViews', 'dateCreated')
    search_fields = ('title',)


@admin.register(VpCategory)
class VpCategoryAdmin(admin.ModelAdmin):
    list_display = ('category',)
    search_fields = ('category',)


@admin.register(Vocabulary)
class VocabularyAdmin(admin.ModelAdmin):
    list_display = ('vocabulary', 'category', 'theme')
    list_filter = ('category',)
    search_fields = ('vocabulary',)


@admin.register(Phrase)
class PhraseAdmin(admin.ModelAdmin):
    list_display = ('phrase', 'category', 'theme')
    list_filter = ('category',)
    search_fields = ('phrase',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'confirmation_code')
    search_fields = ('user__username',)
